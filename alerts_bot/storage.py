from __future__ import annotations
from typing import Iterable, Optional, Dict, List, Tuple
import time
import json
import hashlib

try:
    import redis  # type: ignore
except Exception:
    redis = None

# Redis key schema (prefixes)
# users:set -> all user ids
# user:{uid}:hash -> {username, spread_threshold, delta_threshold, summary_on, role}
# subs:{uid}:set -> internal_sku subscribed by user
# sku_subs:{sku}:set -> users subscribed to sku
# admin:superusers:set -> superuser ids
# alert:sent:{type}:{sku}:{uid}:{bucket} -> de-dup marker
# locks:{name} -> ephemeral lock keys

class RedisStorage:
    def __init__(self, redis_url: str):
        if not redis:
            raise RuntimeError("Redis library not available")
        self.r = redis.Redis.from_url(redis_url, decode_responses=True)

    # ---------- users & roles ----------
    def register_user(self, uid: int, username: str) -> None:
        pipe = self.r.pipeline()
        pipe.sadd("users:set", uid)
        pipe.hsetnx(f"user:{uid}:hash", "role", "user")
        pipe.hset(f"user:{uid}:hash", mapping={
            "username": username or "",
        })
        pipe.execute()

    def get_user(self, uid: int) -> dict:
        data = self.r.hgetall(f"user:{uid}:hash") or {}
        data["id"] = uid
        data.setdefault("role", "user")
        data.setdefault("spread_threshold", "")
        data.setdefault("delta_threshold", "")
        data.setdefault("summary_on", "0")
        return data

    def set_superusers_initial(self, ids: Iterable[int]) -> None:
        if not ids:
            return
        self.r.sadd("admin:superusers:set", *list(ids))

    def is_superuser(self, uid: int) -> bool:
        return self.r.sismember("admin:superusers:set", uid)

    def promote(self, uid: int) -> bool:
        return bool(self.r.sadd("admin:superusers:set", uid))

    def demote(self, uid: int) -> bool:
        return bool(self.r.srem("admin:superusers:set", uid))

    # ---------- thresholds & prefs ----------
    def set_thresholds(self, uid: int, spread: Optional[float] = None, delta: Optional[float] = None) -> None:
        mapping = {}
        if spread is not None:
            mapping["spread_threshold"] = str(spread)
        if delta is not None:
            mapping["delta_threshold"] = str(delta)
        if mapping:
            self.r.hset(f"user:{uid}:hash", mapping=mapping)

    def get_thresholds(self, uid: int, default_spread: float, default_delta: float) -> Tuple[float, float]:
        h = self.r.hgetall(f"user:{uid}:hash") or {}
        s = float(h.get("spread_threshold", "") or default_spread)
        d = float(h.get("delta_threshold", "") or default_delta)
        return s, d

    def set_summary(self, uid: int, on: bool) -> None:
        self.r.hset(f"user:{uid}:hash", "summary_on", "1" if on else "0")

    # ---------- subscriptions ----------
    def subscribe(self, uid: int, sku: str) -> None:
        pipe = self.r.pipeline()
        pipe.sadd(f"subs:{uid}:set", sku)
        pipe.sadd("all:subs:skus:set", sku)
        pipe.sadd(f"sku_subs:{sku}:set", uid)
        pipe.execute()

    def unsubscribe(self, uid: int, sku: str) -> None:
        pipe = self.r.pipeline()
        pipe.srem(f"subs:{uid}:set", sku)
        pipe.srem(f"sku_subs:{sku}:set", uid)
        pipe.execute()

    def list_subscriptions(self, uid: int) -> List[str]:
        return sorted(self.r.smembers(f"subs:{uid}:set"))

    def subscribers_of(self, sku: str) -> List[int]:
        return [int(x) for x in self.r.smembers(f"sku_subs:{sku}:set")]

    def all_users(self) -> List[int]:
        return [int(x) for x in self.r.smembers("users:set")]

    def all_subscribed_skus(self) -> List[str]:
        return list(self.r.smembers("all:subs:skus:set"))

    # ---------- dedup & locks ----------
    def _alert_bucket(self, window_seconds: int = 3600) -> str:
        now = int(time.time())
        return str(now // window_seconds)

    def mark_alert_if_new(self, alert_type: str, sku: str, uid: int, payload_hash: str, ttl: int = 7200) -> bool:
        bucket = self._alert_bucket()
        key = f"alert:sent:{alert_type}:{sku}:{uid}:{bucket}:{payload_hash}"
        # set if not exists with ttl
        ok = self.r.set(key, "1", ex=ttl, nx=True)
        return bool(ok)

    def try_lock(self, name: str, ttl: int = 120) -> bool:
        return bool(self.r.set(f"locks:{name}", "1", ex=ttl, nx=True))

    def release_lock(self, name: str) -> None:
        self.r.delete(f"locks:{name}")

    # ---------- metrics (ops) ----------
    def superusers_list(self) -> List[int]:
        return [int(x) for x in self.r.smembers("admin:superusers:set")] 

    def incr_hourly_counter(self, metric: str, amount: int = 1, ttl_hours: int = 48) -> None:
        """Incrementa un contador por hora: metrics:hourly:{metric}:{bucket}.
        Mantiene TTL para poder sumar últimas N horas sin crecer indefinidamente.
        """
        bucket = self._alert_bucket(3600)
        key = f"metrics:hourly:{metric}:{bucket}"
        pipe = self.r.pipeline()
        pipe.incrby(key, amount)
        pipe.expire(key, ttl_hours * 3600)
        pipe.execute()

    def hourly_counter_sum(self, metric: str, last_n: int = 24) -> int:
        """Suma los últimos N buckets horarios del contador dado."""
        now_bucket = int(self._alert_bucket(3600))
        total = 0
        for i in range(last_n):
            b = now_bucket - i
            v = self.r.get(f"metrics:hourly:{metric}:{b}")
            if v and v.isdigit():
                total += int(v)
        return total

    def set_metric_value(self, name: str, value: str, ttl_seconds: int = 86400) -> None:
        self.r.set(f"metrics:value:{name}", value, ex=ttl_seconds)

    def get_metric_value(self, name: str) -> str:
        return self.r.get(f"metrics:value:{name}") or ""

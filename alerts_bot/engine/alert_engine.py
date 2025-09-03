from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Iterable
import hashlib

from .rules import Thresholds, trigger_spread, trigger_intraday
from .templates import format_spread_msg, format_intraday_msg

@dataclass
class Alert:
    user_id: int
    internal_sku: str
    canonical_name: str
    payload: Dict[str, Any]
    type: str  # 'spread' | 'intraday'
    message: str

class AlertEngine:
    def __init__(self, storage, repo, notifier, default_spread: float, default_delta: float):
        self.storage = storage
        self.repo = repo
        self.notifier = notifier
        self.th_defaults = Thresholds(default_spread, default_delta)

    async def evaluate_and_send(self, shard_total: int = 1, shard_index: int = 0):
        # Construir mapping SKU -> [user_ids] considerando sharding
        sku_to_users = {}
        for sku in self.storage.all_subscribed_skus():
            if shard_total > 1:
                if (hash(sku) % shard_total) != shard_index:
                    continue
            subs = self.storage.subscribers_of(sku)
            if subs:
                sku_to_users[sku] = subs

        if not sku_to_users:
            return

        # Consulta y difusión
        for sku, users in sku_to_users.items():
            spread_stats = self.repo.current_spread(sku)
            delta_stats = self.repo.intraday_delta(sku)

            # obtener nombre canónico (mejor esfuerzo)
            canonical_name = self._canonical_name_for(sku)

            for uid in users:
                s_th, d_th = self.storage.get_thresholds(uid, self.th_defaults.spread_pct, self.th_defaults.delta_pct)
                th = Thresholds(s_th, d_th)

                # spread
                payload = trigger_spread(spread_stats, th)
                if payload:
                    msg = format_spread_msg(sku, canonical_name, payload)
                    payload_hash = self._hash_payload(payload)
                    if self.storage.mark_alert_if_new("spread", sku, uid, payload_hash):
                        # métricas de alertas
                        try:
                            self.storage.incr_hourly_counter("alerts_sent")
                            self.storage.incr_hourly_counter("alerts_sent_spread")
                        except Exception:
                            pass
                        await self.notifier.send_markdown(uid, msg)

                # intraday
                payload = trigger_intraday(delta_stats, th)
                if payload:
                    msg = format_intraday_msg(sku, canonical_name, payload)
                    payload_hash = self._hash_payload(payload)
                    if self.storage.mark_alert_if_new("intraday", sku, uid, payload_hash):
                        # métricas de alertas
                        try:
                            self.storage.incr_hourly_counter("alerts_sent")
                            self.storage.incr_hourly_counter("alerts_sent_intraday")
                        except Exception:
                            pass
                        await self.notifier.send_markdown(uid, msg)

    def _hash_payload(self, payload: Dict[str, Any]) -> str:
        s = str(sorted(payload.items()))
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def _canonical_name_for(self, sku: str) -> str:
        # mejor esfuerzo desde parquet de products
        try:
            rows = self.repo.con.execute(
                """SELECT normalized_name FROM read_parquet($parquet)/normalized/products/*.parquet WHERE internal_sku = ? LIMIT 1"""
                .replace("$parquet", self.repo.parquet_root)
            , [sku]).fetchall()
            if rows:
                return rows[0][0]
        except Exception:
            pass
        return sku

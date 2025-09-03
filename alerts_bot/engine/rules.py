from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Thresholds:
    spread_pct: float
    delta_pct: float

def trigger_spread(spread_stats: Dict[str, Any], th: Thresholds) -> Optional[Dict[str, Any]]:
    if not spread_stats:
        return None
    spread = float(spread_stats.get("spread_pct") or 0.0)
    rc = int(spread_stats.get("retailer_count") or 0)
    if rc < 2:
        return None
    if spread >= th.spread_pct:
        return {
            "type": "spread",
            "spread_pct": spread,
            "min_price": float(spread_stats.get("min_price")),
            "max_price": float(spread_stats.get("max_price")),
            "retailer_count": rc,
        }
    return None

def trigger_intraday(delta_stats: Dict[str, Any], th: Thresholds) -> Optional[Dict[str, Any]]:
    if not delta_stats:
        return None
    delta_pct = float(delta_stats.get("delta_pct") or 0.0)
    if delta_pct >= th.delta_pct:
        return {
            "type": "intraday",
            "retailer": delta_stats.get("retailer"),
            "delta_pct": delta_pct,
            "min_24h": float(delta_stats.get("min_24h") or 0.0),
            "max_24h": float(delta_stats.get("max_24h") or 0.0),
        }
    return None

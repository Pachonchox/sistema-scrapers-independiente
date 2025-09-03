from __future__ import annotations
import os
from dataclasses import dataclass

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class BotConfig:
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    # PostgreSQL es el único backend ahora (todo migrado)
    data_backend: str = "postgres"
    # PostgreSQL DSN (e.g., postgresql://user:pass@localhost:5432/dbname)
    database_url: str = os.getenv("DATABASE_URL", os.getenv("PG_DSN", ""))

    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    default_spread_threshold: float = float(os.getenv("ALERT_SPREAD_THRESHOLD_DEFAULT", "0.05"))
    default_delta_threshold: float = float(os.getenv("ALERT_DELTA_THRESHOLD_DEFAULT", "0.10"))

    shard_total: int = int(os.getenv("SHARD_TOTAL", "1"))
    shard_index: int = int(os.getenv("SHARD_INDEX", "0"))

    superusers_env: str = os.getenv("SUPERUSERS", "")

    def superusers(self) -> list[int]:
        ids = []
        for token in self.superusers_env.split(","):
            token = token.strip()
            if token.isdigit():
                ids.append(int(token))
        return ids

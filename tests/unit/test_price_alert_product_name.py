import pytest
from datetime import date
from unittest.mock import AsyncMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.product_processor import ProductProcessor, ProcessingStats
import core.product_processor as pp


class DummyPriceManager:
    def get_price_record_date(self):
        return date.today()

    def should_update_price(self, fecha):
        return True


class DummyCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, query, params):
        self.executed.append((query, params))

    def fetchall(self):
        return self.rows


@pytest.mark.asyncio
async def test_price_change_alert_uses_correct_product_name(monkeypatch):
    processor = ProductProcessor.__new__(ProductProcessor)
    processor.cursor = DummyCursor([
        ("SKU1", 1000, 900, None),
        ("SKU2", 500, 400, None),
    ])
    processor.price_manager = DummyPriceManager()
    processor.stats = ProcessingStats()

    mock_alert = AsyncMock()
    processor._send_price_change_alert = mock_alert

    monkeypatch.setattr(pp, "ALERTS_AVAILABLE", True)

    # Dummy execute_values to avoid DB operations
    captured = {}

    def fake_execute_values(cursor, query, args):
        captured["args"] = args

    monkeypatch.setattr(pp, "execute_values", fake_execute_values)

    products = [
        ("SKU1", {"name": "Product One", "original_price": 1000, "current_price": 800}, "retA"),
        ("SKU2", {"name": "Product Two", "original_price": 500, "current_price": 350}, "retB"),
    ]

    await ProductProcessor._process_prices_batch(processor, products)

    names = [call.args[1] for call in mock_alert.await_args_list]
    assert names == ["Product One", "Product Two"]

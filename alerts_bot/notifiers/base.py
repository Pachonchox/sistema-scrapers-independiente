from __future__ import annotations
from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    async def send_markdown(self, user_id: int, text: str) -> None:
        ...

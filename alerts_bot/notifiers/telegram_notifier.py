from __future__ import annotations
from typing import Optional
from .base import Notifier

class TelegramNotifier(Notifier):
    def __init__(self, application):
        self.application = application  # python-telegram-bot Application

    async def send_markdown(self, user_id: int, text: str) -> None:
        await self.application.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

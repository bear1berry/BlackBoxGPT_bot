from __future__ import annotations
import asyncio
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from aiogram import Bot
from aiogram.types import Message
from zoneinfo import ZoneInfo
from .config import DATA_DIR

logger = logging.getLogger(__name__)

# Simplified Storage for Reminders (in same DB or separate)
DB_PATH = DATA_DIR / "aimedbot.db"

@dataclass
class ReminderSpec:
    text: str
    fire_at: float

class ReminderStorage:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY, chat_id INTEGER, text TEXT, fire_at REAL, is_active INTEGER DEFAULT 1
                )
            """)
    
    def add(self, chat_id, text, fire_at):
        with self.conn:
            self.conn.execute("INSERT INTO reminders (chat_id, text, fire_at) VALUES (?,?,?)", (chat_id, text, fire_at))

    def get_due(self):
        now = time.time()
        return self.conn.execute("SELECT * FROM reminders WHERE is_active=1 AND fire_at <= ?", (now,)).fetchall()

    def deactivate(self, rid):
        with self.conn:
            self.conn.execute("UPDATE reminders SET is_active=0 WHERE id=?", (rid,))

class ReminderService:
    def __init__(self, storage: ReminderStorage):
        self.storage = storage

    async def try_handle_message(self, user_id: int, text: str, user_timezone="Europe/Moscow") -> str | None:
        """Simple regex parser for 'remind me in X min'"""
        match = re.search(r"(напомни|remind)\s+(через|in)\s+(\d+)\s*(мин|min)", text.lower())
        if match:
            mins = int(match.group(3))
            fire_at = time.time() + mins * 60
            clean_text = text # In real app, clean the trigger words
            self.storage.add(user_id, clean_text, fire_at)
            return f"⏰ Напоминание установлено через {mins} минут."
        return None

class ReminderScheduler:
    def __init__(self, bot: Bot, storage: ReminderStorage):
        self.bot = bot
        self.storage = storage
        self._task = None
    
    def start(self):
        self._task = asyncio.create_task(self.loop())
    
    async def stop(self):
        if self._task: self._task.cancel()
    
    async def loop(self):
        while True:
            await asyncio.sleep(10)
            rows = self.storage.get_due()
            for r in rows:
                try:
                    await self.bot.send_message(r['chat_id'], f"🔔 <b>Напоминание:</b>\n{r['text']}", parse_mode="HTML")
                    self.storage.deactivate(r['id'])
                except Exception as e:
                    logger.error(f"Failed to send reminder: {e}")

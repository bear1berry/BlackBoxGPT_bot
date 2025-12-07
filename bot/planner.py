from __future__ import annotations
import logging
import sqlite3
import json
import time
from typing import List, Optional, Dict, Any
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import DATA_DIR

logger = logging.getLogger(__name__)
PLANNER_DB_PATH = DATA_DIR / "planner.db"

# --- Models ---
class PlannerStorage:
    def __init__(self, path=PLANNER_DB_PATH):
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    status TEXT DEFAULT 'todo', -- todo, in_progress, done
                    created_at REAL
                )
            """)

    async def connect(self): pass # Stub for async compatibility
    async def close(self): self.conn.close()

    def add_task(self, user_id: int, title: str):
        with self.conn:
            self.conn.execute("INSERT INTO tasks (user_id, title, created_at) VALUES (?, ?, ?)", 
                              (user_id, title, time.time()))

    def get_tasks(self, user_id: int, status: str = None):
        if status:
            return self.conn.execute("SELECT * FROM tasks WHERE user_id=? AND status=?", (user_id, status)).fetchall()
        return self.conn.execute("SELECT * FROM tasks WHERE user_id=? AND status != 'done'", (user_id,)).fetchall()

    def update_status(self, task_id: int, status: str):
        with self.conn:
            self.conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))

# --- AI Parser (Mock logic for speed, can be connected to LLM) ---
class PlannerAIParser:
    async def parse_command(self, text: str) -> Dict[str, Any]:
        """Simple heuristic parser to avoid heavy LLM calls for basic tasks."""
        text = text.lower()
        if text.startswith("добавить задачу") or text.startswith("задача"):
            clean = text.replace("добавить задачу", "").replace("задача", "").strip()
            return {"action": "add", "title": clean}
        return {"action": "unknown"}

# --- Service ---
class PlannerService:
    def __init__(self, storage: PlannerStorage, parser: PlannerAIParser):
        self.storage = storage
        self.parser = parser

    async def handle_text(self, user_id: int, text: str) -> Optional[str]:
        parse_res = await self.parser.parse_command(text)
        if parse_res['action'] == 'add' and parse_res['title']:
            self.storage.add_task(user_id, parse_res['title'])
            return f"✅ Задача добавлена: {parse_res['title']}"
        return None

# --- Router & UI ---
router = Router(name="planner")
_service: Optional[PlannerService] = None

def setup_planner_router(service: PlannerService) -> Router:
    global _service
    _service = service
    return router

def get_planner_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Добавить (напиши текстом)", callback_data="planner:info")],
        [InlineKeyboardButton(text="📋 Список дел", callback_data="planner:list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav:root")]
    ])

@router.callback_query(F.data == "planner:open")
async def open_planner(call: types.CallbackQuery):
    await call.message.edit_text("🗓 **Планировщик задач**\n\nУправляй своими делами.", reply_markup=get_planner_kb(), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "planner:list")
async def list_tasks(call: types.CallbackQuery):
    if not _service: return
    tasks = _service.storage.get_tasks(call.from_user.id)
    if not tasks:
        await call.message.edit_text("Список задач пуст.", reply_markup=get_planner_kb())
        return
    
    text = "📋 **Твои задачи:**\n\n"
    kb = []
    for t in tasks:
        icon = "⬜" if t['status'] == 'todo' else "construction"
        text += f"{icon} {t['title']}\n"
        kb.append([InlineKeyboardButton(text=f"✅ {t['title'][:20]}", callback_data=f"planner:done:{t['id']}")])
    
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="planner:open")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@router.callback_query(F.data.startswith("planner:done:"))
async def complete_task(call: types.CallbackQuery):
    tid = int(call.data.split(":")[-1])
    _service.storage.update_status(tid, "done")
    await call.answer("Задача выполнена!")
    await list_tasks(call)

@router.callback_query(F.data == "planner:info")
async def planner_info(call: types.CallbackQuery):
    await call.answer("Просто напиши: 'Задача купить молоко'", show_alert=True)

# Helper for main
def get_planner_storage_from_env():
    return PlannerStorage()

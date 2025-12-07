from __future__ import annotations
import sqlite3
import json
import time
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from .config import DATA_DIR, ADMIN_IDS

logger = logging.getLogger(__name__)
DB_PATH = DATA_DIR / "aimedbot.db"

@dataclass
class UserRecord:
    id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_bot: bool = False
    mode_key: str = "universal"
    plan_code: str = "free"
    premium_until: Optional[str] = None
    daily_used: int = 0
    ref_code: Optional[str] = None
    referrals_count: int = 0
    referrer_user_id: Optional[int] = None
    last_invoice_id: Optional[int] = None
    last_tariff_key: Optional[str] = None
    ab_strategy: str = "A"
    
    @property
    def full_name(self) -> str:
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) or "User"

class Storage:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cur = self._conn.cursor()
        # Users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT, first_name TEXT, last_name TEXT,
                is_bot INTEGER DEFAULT 0,
                mode_key TEXT DEFAULT 'universal',
                plan_code TEXT DEFAULT 'free',
                premium_until TEXT,
                daily_used INTEGER DEFAULT 0,
                daily_date TEXT,
                ref_code TEXT,
                referrals_count INTEGER DEFAULT 0,
                referrer_user_id INTEGER,
                last_invoice_id INTEGER,
                last_tariff_key TEXT,
                ab_strategy TEXT,
                created_at REAL, updated_at REAL
            )
        """)
        # Messages (Logs)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, role TEXT, content TEXT, created_at REAL, feedback_tag TEXT
            )
        """)
        self._conn.commit()

    def get_or_create_user(self, user_id: int, tg_user) -> Tuple[UserRecord, bool]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        created = False
        now = time.time()
        
        if not row:
            created = True
            cur.execute("""
                INSERT INTO users (id, username, first_name, last_name, is_bot, created_at, updated_at, ref_code, ab_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, tg_user.username, tg_user.first_name, tg_user.last_name, 
                1 if tg_user.is_bot else 0, now, now, f"BB{user_id}", "A"
            ))
            self._conn.commit()
            cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
            row = cur.fetchone()

        # Check daily reset
        today = time.strftime("%Y-%m-%d")
        if row["daily_date"] != today:
            cur.execute("UPDATE users SET daily_used=0, daily_date=? WHERE id=?", (today, user_id))
            self._conn.commit()
            row = self._fetch_user_row(user_id) # reload

        user = UserRecord(
            id=row['id'], username=row['username'], first_name=row['first_name'], last_name=row['last_name'],
            is_bot=bool(row['is_bot']), mode_key=row['mode_key'] or "universal",
            plan_code=row['plan_code'] or "free", premium_until=row['premium_until'],
            daily_used=row['daily_used'], ref_code=row['ref_code'],
            referrals_count=row['referrals_count'], referrer_user_id=row['referrer_user_id'],
            last_invoice_id=row['last_invoice_id'], last_tariff_key=row['last_tariff_key'],
            ab_strategy=row['ab_strategy'] or "A"
        )
        return user, created

    def _fetch_user_row(self, uid):
        return self._conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

    def save_user(self, user: UserRecord):
        # Simplified update
        self._conn.execute("""
            UPDATE users SET mode_key=?, plan_code=?, premium_until=?, daily_used=?, 
            referrals_count=?, last_invoice_id=?, last_tariff_key=?, updated_at=?
            WHERE id=?
        """, (
            user.mode_key, user.plan_code, user.premium_until, user.daily_used,
            user.referrals_count, user.last_invoice_id, user.last_tariff_key, time.time(), user.id
        ))
        self._conn.commit()

    def log_message(self, user_id, role, content):
        self._conn.execute("INSERT INTO messages (user_id, role, content, created_at) VALUES (?,?,?,?)",
                           (user_id, role, content, time.time()))
        self._conn.commit()

    def is_admin(self, user_id: int) -> bool:
        return user_id in ADMIN_IDS

    def effective_plan(self, user: UserRecord, is_admin: bool) -> str:
        if is_admin: return "admin"
        if user.premium_until and user.premium_until >= time.strftime("%Y-%m-%d"):
            return "premium"
        return "free"
    
    def apply_usage(self, user: UserRecord, tokens_used: int = 0):
        user.daily_used += 1
        self.save_user(user)

    def set_mode(self, user_id: int, mode_key: str):
        self._conn.execute("UPDATE users SET mode_key=? WHERE id=?", (mode_key, user_id))
        self._conn.commit()
    
    # Subscription logic helpers
    def store_invoice(self, user: UserRecord, invoice_id: int, tariff_key: str):
        user.last_invoice_id = invoice_id
        user.last_tariff_key = tariff_key
        self.save_user(user)

    def get_last_invoice(self, user: UserRecord):
        return user.last_invoice_id, user.last_tariff_key

    def activate_premium(self, user: UserRecord, months: int):
        from datetime import date, timedelta, datetime
        base = date.today()
        if user.premium_until:
            try:
                curr = datetime.strptime(user.premium_until, "%Y-%m-%d").date()
                if curr > base: base = curr
            except: pass
        
        new_date = base + timedelta(days=30*months)
        user.premium_until = new_date.strftime("%Y-%m-%d")
        user.plan_code = "premium"
        self.save_user(user)
        
    def apply_referral(self, new_user_id, ref_code):
        row = self._conn.execute("SELECT * FROM users WHERE ref_code=?", (ref_code,)).fetchone()
        if row and row['id'] != new_user_id:
            # Simple referral logic: +1 count
            cnt = row['referrals_count'] + 1
            self._conn.execute("UPDATE users SET referrals_count=? WHERE id=?", (cnt, row['id']))
            self._conn.execute("UPDATE users SET referrer_user_id=? WHERE id=?", (row['id'], new_user_id))
            self._conn.commit()

import asyncpg
from bot.config import settings

async def init_db():
    conn = await asyncpg.connect(settings.DB_DSN)
    try:
        # Создаем таблицы, если их нет (вместо миграций, для простоты)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_mode TEXT DEFAULT 'universal',
                style_formality INTEGER DEFAULT 50,
                style_emotionality INTEGER DEFAULT 50,
                style_verbosity INTEGER DEFAULT 50
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                is_premium BOOLEAN DEFAULT FALSE,
                subscription_expires_at TIMESTAMP
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                referral_id SERIAL PRIMARY KEY,
                referrer_id BIGINT REFERENCES users(user_id),
                referred_id BIGINT REFERENCES users(user_id),
                referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                amount NUMERIC(10, 2),
                currency TEXT,
                status TEXT,
                invoice_id TEXT,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS usage_stats (
                user_id BIGINT REFERENCES users(user_id),
                date DATE DEFAULT CURRENT_DATE,
                request_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS dialogs (
                dialog_id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                message TEXT,
                response TEXT,
                tokens_used INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    finally:
        await conn.close()

async def get_connection():
    return await asyncpg.connect(settings.DB_DSN)

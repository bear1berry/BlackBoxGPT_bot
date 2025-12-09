-- Базовая структура таблиц (совпадает с SQLAlchemy-моделями)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at DATETIME NOT NULL,
    current_mode VARCHAR(32) NOT NULL DEFAULT 'universal',
    profile_bio TEXT NOT NULL DEFAULT '',
    subscription_type VARCHAR(16) NOT NULL DEFAULT 'free',
    subscription_until DATETIME,
    referral_code VARCHAR(64) UNIQUE,
    referred_by INTEGER,
    wants_motivation BOOLEAN NOT NULL DEFAULT 0,
    wants_science_facts BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider VARCHAR(16) NOT NULL,
    plan VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL,
    amount VARCHAR(32),
    currency VARCHAR(16),
    invoice_id VARCHAR(128),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    referred_user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (referred_user_id) REFERENCES users (id) ON DELETE CASCADE
);

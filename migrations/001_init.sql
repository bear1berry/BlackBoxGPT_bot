-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    telegram_id     BIGINT UNIQUE NOT NULL,
    username        TEXT,
    first_name      TEXT,
    last_name       TEXT,
    referral_code   TEXT UNIQUE,
    referrer_id     BIGINT REFERENCES users(id),

    current_mode    TEXT NOT NULL DEFAULT 'universal',

    is_premium      BOOLEAN NOT NULL DEFAULT FALSE,
    premium_until   TIMESTAMPTZ,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Подписки
CREATE TABLE IF NOT EXISTS subscriptions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id),
    plan_code   TEXT NOT NULL,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    payment_id  BIGINT
);

-- Рефералка (бонусы можно расширить позже)
CREATE TABLE IF NOT EXISTS referrals (
    id           BIGSERIAL PRIMARY KEY,
    referrer_id  BIGINT NOT NULL REFERENCES users(id),
    referee_id   BIGINT NOT NULL REFERENCES users(id),
    reward_type  TEXT NOT NULL,
    reward_value INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Платежи Crypto Pay
CREATE TABLE IF NOT EXISTS payments (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id),
    invoice_id BIGINT NOT NULL,
    plan_code  TEXT NOT NULL,
    amount     NUMERIC(18,8) NOT NULL,
    asset      TEXT NOT NULL,
    status     TEXT NOT NULL,
    pay_url    TEXT NOT NULL,
    raw        JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at    TIMESTAMPTZ
);

-- Статистика использования (лимиты)
CREATE TABLE IF NOT EXISTS usage_stats (
    user_id       BIGINT NOT NULL REFERENCES users(id),
    day           DATE   NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, day)
);

-- updated_at триггер
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_set_updated_at ON users;

CREATE TRIGGER trg_users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- users
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username    TEXT,
    is_premium  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(id),
    tier          TEXT   NOT NULL,
    status        TEXT   NOT NULL,
    premium_until TIMESTAMPTZ,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- daily_limits
CREATE TABLE IF NOT EXISTS daily_limits (
    user_id        BIGINT NOT NULL REFERENCES users(id),
    day            DATE   NOT NULL,
    used_requests  INT    NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, day)
);

PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users(
  user_id INTEGER PRIMARY KEY,
  created_at INTEGER NOT NULL,
  last_seen INTEGER NOT NULL DEFAULT 0,

  mode TEXT NOT NULL DEFAULT 'universal', -- universal | pro
  plan TEXT NOT NULL DEFAULT 'basic',     -- basic | premium
  premium_until INTEGER NOT NULL DEFAULT 0,

  trial_used INTEGER NOT NULL DEFAULT 0, -- for basic trial
  daily_used INTEGER NOT NULL DEFAULT 0, -- for premium daily
  daily_date TEXT NOT NULL DEFAULT '',   -- YYYY-MM-DD

  style_json TEXT NOT NULL DEFAULT '{}',
  long_memory TEXT NOT NULL DEFAULT '',

  ref_code TEXT NOT NULL,
  referrer_id INTEGER,

  checkin_enabled INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_users_referrer ON users(referrer_id);

CREATE TABLE IF NOT EXISTS invoices(
  invoice_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  months INTEGER NOT NULL,
  amount REAL NOT NULL,
  asset TEXT NOT NULL DEFAULT 'USDT',
  status TEXT NOT NULL,
  pay_url TEXT,
  created_at INTEGER NOT NULL,
  paid_at INTEGER NOT NULL DEFAULT 0,
  raw_json TEXT NOT NULL DEFAULT '',
  FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);

CREATE TABLE IF NOT EXISTS continues(
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  parts_json TEXT NOT NULL,
  idx INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS memory(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  ts INTEGER NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_memory_user_ts ON memory(user_id, ts);

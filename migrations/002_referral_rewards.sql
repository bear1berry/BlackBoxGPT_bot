ALTER TABLE invoices ADD COLUMN rewarded INTEGER NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_invoices_rewarded ON invoices(rewarded);

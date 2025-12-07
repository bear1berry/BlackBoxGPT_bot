-- migrations/002_planner_init.sql
-- Дублирует базовую схему для совместимости с командой:
-- psql "$PLANNER_DATABASE_URL" -f migrations/002_planner_init.sql

\i migrations/001_init.sql

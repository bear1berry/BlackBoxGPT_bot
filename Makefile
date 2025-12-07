.PHONY: run migrate lint

run:
	python -m bot.main

migrate:
	psql "$PLANNER_DATABASE_URL" -f migrations/002_planner_init.sql

lint:
	python -m compileall bot

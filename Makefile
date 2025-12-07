.PHONY: run migrate lint

run:
\tpython -m bot.main

migrate:
\tpsql "$$PLANNER_DATABASE_URL" -f migrations/002_planner_init.sql

lint:
\tpython -m compileall bot

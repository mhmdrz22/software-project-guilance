#!/bin/bash
set -e

echo "Resetting database state..."

# 1. Remove migration files (except __init__.py)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete

# 2. Remove SQLite db if it exists (for local runs)
rm -f db.sqlite3

# 3. Remake migrations
python manage.py makemigrations

# 4. Migrate
python manage.py migrate

echo "Database reset complete."

"""Run once on startup to initialize the database."""
import os
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not DATABASE_URL:
    print("No DATABASE_URL set — skipping DB init")
    sys.exit(0)

# Import and run init
from app import init_db
init_db()
print("Database initialized OK")

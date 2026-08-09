import sys
from pathlib import Path

# Allow this file to be run directly with: python scripts/migrate.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import close_pool, run_migrations


if __name__ == "__main__":
    try:
        run_migrations()
        print("Database migration complete.")
    finally:
        close_pool()

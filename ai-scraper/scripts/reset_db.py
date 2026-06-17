"""
Database Reset Script — drops all tables and recreates them from models.

Usage:
    python scripts/reset_db.py          # Interactive confirmation
    python scripts/reset_db.py --yes    # Skip confirmation (CI / scripting)

⚠️  This destroys ALL data. Only use in development.
"""

import asyncio
import sys
import os

# Ensure project root is on the path so app.* imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.database import engine, Base

# Import all models so Base.metadata knows every table
from app.models import User, Batch, Company  # noqa: F401


async def reset_database():
    """Drop and recreate all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def main():
    if settings.ENVIRONMENT != "development":
        print(f"❌ Refusing to reset in '{settings.ENVIRONMENT}' environment.")
        print("   Set ENVIRONMENT=development in .env to allow resets.")
        sys.exit(1)

    skip_confirm = "--yes" in sys.argv or "-y" in sys.argv

    if not skip_confirm:
        db_url = str(settings.DATABASE_URL).split("@")[-1]  # hide credentials
        print(f"⚠️  This will DROP ALL TABLES in: …@{db_url}")
        answer = input("   Type 'yes' to confirm: ").strip().lower()
        if answer != "yes":
            print("Aborted.")
            sys.exit(0)

    print("Dropping all tables…")
    asyncio.run(reset_database())
    print("✅ All tables dropped and recreated successfully.")


if __name__ == "__main__":
    main()

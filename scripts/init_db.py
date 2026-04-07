"""Initialize database with first admin user.

Usage: docker compose exec api python -m scripts.init_db
Or:    python scripts/init_db.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings
from app.database import engine, async_session, Base
from app.models import *  # noqa
from app.core.security import hash_password
from app.models.user import User


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create admin user if not exists
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.email == "admin@unicab.it"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@unicab.it",
                hashed_password=hash_password("changeme"),
                full_name="UNICAB Admin",
                is_admin=True,
            )
            session.add(admin)
            await session.commit()
            print("Admin user created: admin@unicab.it")
        else:
            print("Admin user already exists.")

    print("Database initialized.")


if __name__ == "__main__":
    asyncio.run(init())

"""
Database configuration and session management.

Uses SQLAlchemy 2.0 (async mode) as the ORM.
SQLAlchemy is Python's most popular ORM — like ActiveRecord in Rails, but more explicit.

Key concepts for a Rails developer:
  - Engine     = database connection pool (like Rails' connection_pool)
  - Session    = a unit of work / transaction (like ActiveRecord's implicit transaction)
  - Base       = parent class for all models (like ApplicationRecord)
  - Alembic    = migration tool (like db:migrate in Rails)

We use ASYNC versions (AsyncSession, create_async_engine) because:
  - FastAPI is async-native
  - Allows handling many requests without blocking
  - Requires 'asyncpg' driver (async PostgreSQL driver) instead of 'psycopg2'


  Quick Reference: SQLAlchemy vs ActiveRecord
    Rails (ActiveRecord)    Python (SQLAlchemy)
    User.find(1)            await db.get(User, 1)
    User.where(name: "x")   await db.execute(select(User).where(User.name == "x"))
    user.save               db.add(user); await db.commit()
    user.update(name: "y")  user.name = "y"; await db.commit()
    user.destroy            await db.delete(user); await db.commit()
    User.create(...)        db.add(User(...)); await db.commit()
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,       # Async version of SQLAlchemy Session
    create_async_engine, # Creates async DB connection pool
    async_sessionmaker,  # Factory for creating async sessions
)
from sqlalchemy.orm import DeclarativeBase  # Base class for ORM models

from app.config import settings


# ---------------------------------------------------------------
# Engine: Manages the connection pool to PostgreSQL.
#
# - pool_size=5: Keep 5 connections open and ready (like Rails pool size)
# - max_overflow=10: Allow up to 10 extra connections during spikes
# - echo=True in debug: Logs all SQL queries (like Rails SQL logging)
# ---------------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,  # Print SQL queries when DEBUG=True
)


# ---------------------------------------------------------------
# SessionFactory: Creates new database sessions.
#
# In Rails, ActiveRecord manages sessions implicitly.
# In SQLAlchemy, you explicitly create and close sessions.
#
# - expire_on_commit=False: After committing, objects stay usable
#   without hitting the DB again. Without this, accessing any
#   attribute after commit would trigger a lazy load (and fail in async).
# ---------------------------------------------------------------
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------
# Base: All ORM models inherit from this.
# Equivalent to Rails' ApplicationRecord.
#
# Example:
#   class Company(Base):
#       __tablename__ = "companies"
#       id = Column(Integer, primary_key=True)
# ---------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------
# get_db: Dependency injection for FastAPI routes.
#
# FastAPI uses "dependency injection" to provide a DB session
# to each request. This function:
#   1. Creates a session
#   2. Yields it to the route handler (the route uses it)
#   3. Closes it after the request finishes
#
# In Rails terms: this is like an around_action that wraps each
# request in a database checkout/return cycle.
#
# Usage in a route:
#   @router.get("/companies")
#   async def list_companies(db: AsyncSession = Depends(get_db)):
#       result = await db.execute(select(Company))
#       return result.scalars().all()
#
# "async for" / "yield" pattern = Python's equivalent of
# Ruby's block-with-ensure (File.open { |f| ... })
# ---------------------------------------------------------------
async def get_db():
    """
    Provide a database session for each request.
    Session is automatically closed when the request finishes.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# ---------------------------------------------------------------
# Utility functions for app startup/shutdown.
# Called from FastAPI lifespan events (app/main.py).
# ---------------------------------------------------------------
async def init_db():
    """
    Create all tables defined by ORM models.
    Only used in development. In production, use Alembic migrations.

    Equivalent to Rails' db:schema:load
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Dispose of the connection pool on shutdown.
    Ensures all connections are properly closed.
    """
    await engine.dispose()

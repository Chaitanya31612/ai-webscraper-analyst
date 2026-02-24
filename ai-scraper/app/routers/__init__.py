"""
Routers package — exports all API routers.

FastAPI uses routers to organize endpoints into logical groups.
This is like having separate controller files in Rails.

Each router handles a specific resource:
  - batches.py  → /api/batches/*  (upload, status, confirm)
  - companies.py → /api/companies/* (results, export)

Usage in main.py:
    from app.routers import batches, companies
    app.include_router(batches.router, prefix="/api/batches")
"""

from app.routers import batches
from app.routers import companies

__all__ = ["batches", "companies"]

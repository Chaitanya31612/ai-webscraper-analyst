"""
FastAPI Application Entrypoint.

This is the equivalent of config/application.rb + config.ru in Rails.
It boots the app, registers routes, and manages startup/shutdown.

Run with:
    uvicorn app.main:app --reload

    - uvicorn: ASGI server (like Puma for Rails)
    - app.main:app → file path : variable name
    - --reload: Auto-restart on code changes (like Rails' reloader)
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db


# ---------------------------------------------------------------
# Lifespan: Startup and Shutdown hooks.
#
# In Rails, you'd put startup code in config/initializers/.
# In FastAPI, the "lifespan" context manager runs:
#   - Code before `yield` → on startup
#   - Code after `yield`  → on shutdown
#
# We use it to:
#   1. Create DB tables on startup (dev only)
#   2. Close DB connections on shutdown
# ---------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on app startup and shutdown."""

    # --- STARTUP ---
    print(f"Starting {settings.APP_NAME} ({settings.ENVIRONMENT})")

    # Create upload/output directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    # In development, auto-create tables.
    # In production, use Alembic migrations instead.
    if settings.ENVIRONMENT == "development":
        await init_db()
        print("Database tables created (dev mode)")

    print(f"AI Provider: {settings.DEFAULT_AI_PROVIDER} / {settings.DEFAULT_AI_MODEL}")

    yield  # App is running and serving requests here

    # --- SHUTDOWN ---
    await close_db()
    print("Database connections closed")


# ---------------------------------------------------------------
# Create the FastAPI application.
#
# FastAPI() is like Rails.application — the root app object.
# It handles routing, middleware, dependency injection, etc.
# ---------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    # Disable docs in production
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url=None,
)


# ---------------------------------------------------------------
# CORS Middleware.
#
# Like Rails' rack-cors gem.
# Allows the Vue frontend (on a different port) to call our API.
# ---------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    # In dev, allow all localhost ports. In prod, restrict to your domain.
    allow_origins=(
        [
            "http://localhost:5173",   # Vite default
            "http://localhost:5174",   # Vite fallback port
            "http://localhost:3000",   # Alternative dev port
        ]
        if settings.ENVIRONMENT == "development"
        else []
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------
# Register Routers (like Rails' config/routes.rb)
#
# Each router is a group of related endpoints.
# prefix="/api/batches" → all routes in batches.py start with /api/batches
# tags=["Batches"] → groups them in the auto-generated docs at /api/docs
# ---------------------------------------------------------------
from app.routers import batches, companies, auth
from app.routers import ai as ai_router

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Auth"],
)

app.include_router(
    batches.router,
    prefix="/api/batches",
    tags=["Batches"],
)

app.include_router(
    companies.router,
    prefix="/api/companies",
    tags=["Companies"],
)

app.include_router(
    ai_router.router,
    prefix="/api/ai",
    tags=["AI Utilities"],
)


# ---------------------------------------------------------------
# Health check endpoint.
# Simple route to verify the app is running.
# Useful for load balancers, Docker health checks, uptime monitors.
# ---------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }

"""
Auth Router — register, login, Google OAuth, and /me endpoints.

Endpoints:
  POST /api/auth/register  → create account (email + password)
  POST /api/auth/login     → login, returns JWT
  POST /api/auth/google    → exchange Google auth code for JWT
  GET  /api/auth/me        → get current user (requires Bearer token)
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleAuthRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: build token response from a User
# ---------------------------------------------------------------------------
def _token_response(user: User) -> TokenResponse:
    """Create a TokenResponse with a fresh JWT for the given user."""
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------
@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new account with email + password."""

    # Check if email is already taken
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=body.email.lower().strip(),
        full_name=body.full_name.strip(),
        hashed_password=hash_password(body.password),
        auth_provider="local",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return _token_response(user)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email + password, returns JWT."""

    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return _token_response(user)


# ---------------------------------------------------------------------------
# POST /google — exchange Google authorization code for JWT
# ---------------------------------------------------------------------------
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.post("/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange a Google authorization code for our JWT.

    Flow:
      1. Frontend gets an auth code from Google consent screen
      2. Frontend sends the code here
      3. We exchange it for Google access_token
      4. We fetch user info from Google
      5. We create or link the user, return our JWT
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured on the server",
        )

    # Step 1: Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": body.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": body.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange Google code: {token_resp.text}",
            )
        tokens = token_resp.json()

        # Step 2: Fetch user info
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch Google user info",
            )
        google_user = userinfo_resp.json()

    google_id = google_user["id"]
    email = google_user["email"].lower()
    name = google_user.get("name", email.split("@")[0])
    picture = google_user.get("picture")

    # Step 3: Find or create user
    # First, check by google_id (returning user)
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # Check by email (user exists with local account, link Google)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            # Link Google to existing account
            user.google_id = google_id
            user.avatar_url = picture or user.avatar_url
            if user.auth_provider == "local":
                user.auth_provider = "local"  # keep as local since they also have password
        else:
            # Brand-new Google user
            user = User(
                email=email,
                full_name=name,
                google_id=google_id,
                avatar_url=picture,
                auth_provider="google",
            )
            db.add(user)

    await db.commit()
    await db.refresh(user)

    return _token_response(user)


# ---------------------------------------------------------------------------
# GET /me — current user profile
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)

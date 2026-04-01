# ============================================================
# routers/auth.py — /api/register and /api/login
# ============================================================
# Handles user registration and login.
# Passwords are hashed with SHA-256 before storing.
# (Use bcrypt in production!)
# ============================================================

import hashlib
import secrets

from fastapi import APIRouter, HTTPException
from database import get_connection
from models import RegisterRequest, LoginRequest, AuthResponse, UserInfo

# APIRouter groups these endpoints together.
# The prefix "/api" is added in main.py.
router = APIRouter()


def hash_password(password: str) -> str:
    """
    Convert a plain-text password to a SHA-256 hash string.
    We never store raw passwords in the database.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def make_token() -> str:
    """
    Generate a random 64-character hex token for the session.
    In a real app this would be a JWT — for now it's just a placeholder.
    """
    return secrets.token_hex(32)


# ── POST /api/register ───────────────────────────────────────
@router.post("/register", response_model=AuthResponse)
async def register(data: RegisterRequest):
    """
    Create a new user account.
    - Checks that email/username isn't already taken.
    - Hashes the password.
    - Inserts the new user into the users table.
    - Returns user info + a session token.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Check if this email OR username already exists
    existing = cursor.execute(
        "SELECT id FROM users WHERE email = ? OR username = ?",
        (data.email, data.username)
    ).fetchone()

    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Email or username already taken.")

    # Hash the password before saving
    pw_hash = hash_password(data.password)

    # Insert the new user row
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (data.username, data.email, pw_hash)
    )
    conn.commit()
    new_id = cursor.lastrowid  # the auto-generated ID of the new user
    conn.close()

    return AuthResponse(
        status="ok",
        user=UserInfo(id=new_id, username=data.username, email=data.email),
        token=make_token(),
    )


# ── POST /api/login ──────────────────────────────────────────
@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest):
    """
    Log in an existing user.
    - Finds the user by email.
    - Compares the hashed password.
    - Returns user info + a session token.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Look up the user by email
    user = cursor.execute(
        "SELECT id, username, email, password_hash FROM users WHERE email = ?",
        (data.email,)
    ).fetchone()
    conn.close()

    # Email not found
    if not user:
        raise HTTPException(status_code=404, detail="No account found with that email.")

    # Password mismatch
    if user["password_hash"] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Wrong password.")

    return AuthResponse(
        status="ok",
        user=UserInfo(id=user["id"], username=user["username"], email=user["email"]),
        token=make_token(),
    )

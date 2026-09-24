"""
auth.py — simple user authentication for MIU BEE.
Uses MongoDB for user storage + bcrypt for password hashing
+ itsdangerous for signed session tokens.
Supports role-based permissions: admin, lecturer, viewer.
"""

import os
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import request, jsonify
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

try:
    import db
    MONGO_OK = True
except Exception:
    MONGO_OK = False

SECRET_KEY = os.getenv("SECRET_KEY", "miu-bee-dev-secret-change-me")
COOKIE_NAME = "miu_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

signer = URLSafeTimedSerializer(SECRET_KEY, salt="miu-bee-session")


# ============================================================
# USERS
# ============================================================

def hash_password(plain):
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain, hashed):
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_default_admin():
    """On first run, create admin/miu2026 if no users exist."""
    if not MONGO_OK:
        return
    try:
        if db.col_users().count_documents({}) == 0:
            db.col_users().insert_one({
                "username": "admin",
                "email": "ahuriratech@gmail.com",
                "password_hash": hash_password("miu2026"),
                "role": "admin",
                "created_at": datetime.now(timezone.utc),
            })
            print("[auth] Default admin created: admin / miu2026")
    except Exception as e:
        print(f"[auth] create_default_admin failed: {e}")


def find_user(username):
    if not MONGO_OK:
        return None
    try:
        return db.col_users().find_one({"username": username})
    except Exception:
        return None


# ============================================================
# SESSION TOKENS
# ============================================================

def make_token(username):
    return signer.dumps({"u": username, "n": secrets.token_hex(6)})


def read_token(token):
    try:
        data = signer.loads(token, max_age=COOKIE_MAX_AGE)
        return data.get("u")
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    except Exception:
        return None


def set_session_cookie(response, username):
    token = make_token(username)
    response.set_cookie(
        COOKIE_NAME, token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=False,
    )
    return response


def clear_session_cookie(response):
    response.set_cookie(COOKIE_NAME, "", max_age=0, httponly=True, samesite="Lax")
    return response


def current_user():
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return read_token(token)


# ============================================================
# ROLE SYSTEM
# ============================================================

ROLE_PERMISSIONS = {
    "admin": {
        "generate", "progress", "pdf", "rebuild",
        "cleanup", "cleanup_apply", "stop", "report",
        "search", "dashboard", "download", "zip",
        "manage_users",
    },
    "lecturer": {
        "generate", "progress", "pdf", "rebuild",
        "stop", "report", "search", "dashboard", "download", "zip",
    },
    "viewer": {
        "search", "dashboard", "download", "zip",
    },
}


def user_role(username):
    """Look up a user's role."""
    doc = find_user(username) or {}
    return doc.get("role", "viewer")


def has_permission(username, permission):
    """Check if user has a specific permission via their role."""
    role = user_role(username)
    return permission in ROLE_PERMISSIONS.get(role, set())


# ============================================================
# DECORATORS
# ============================================================

def require_auth(fn):
    """Route decorator: blocks access if not logged in."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


def require_permission(permission):
    """Route decorator: only allows users whose role has the permission."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"ok": False, "error": "Unauthorized"}), 401
            if not has_permission(user, permission):
                return jsonify({
                    "ok": False,
                    "error": (
                        f"Forbidden — your role ({user_role(user)}) "
                        f"cannot perform '{permission}'"
                    )
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles):
    """Route decorator: only allows specific roles."""
    allowed = set(roles)
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"ok": False, "error": "Unauthorized"}), 401
            if user_role(user) not in allowed:
                return jsonify({
                    "ok": False,
                    "error": (
                        f"Forbidden — requires role: {', '.join(sorted(allowed))}"
                    )
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
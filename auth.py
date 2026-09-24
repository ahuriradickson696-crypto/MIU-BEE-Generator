"""
auth.py — simple user authentication for MIU BEE.
Uses MongoDB for user storage + bcrypt for password hashing
+ itsdangerous for signed session tokens.
Supports role-based permissions: admin, lecturer, viewer.
Includes rate limiting + self-service password change.
Cross-domain cookies (SameSite=None; Secure) for Vercel ↔ Render.
"""

import os
import secrets
from datetime import datetime, timezone, timedelta
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

RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_MIN = 15


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


def change_own_password(username, old_password, new_password):
    """Verify old password, then set new one. Returns (ok, message)."""
    user = find_user(username)
    if not user:
        return False, "User not found"
    if not verify_password(old_password, user.get("password_hash", "")):
        return False, "Current password is incorrect"
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters"
    try:
        db.col_users().update_one(
            {"username": username},
            {"$set": {"password_hash": hash_password(new_password)}}
        )
        return True, "Password updated"
    except Exception as e:
        return False, str(e)


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
    """Cross-domain cookie: SameSite=None + Secure (required for Vercel → Render)."""
    token = make_token(username)
    response.set_cookie(
        COOKIE_NAME, token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="None",
        secure=True,
        path="/",
    )
    return response


def clear_session_cookie(response):
    """Clear the session cookie with matching attributes."""
    response.set_cookie(
        COOKIE_NAME, "",
        max_age=0,
        httponly=True,
        samesite="None",
        secure=True,
        path="/",
    )
    return response


def current_user():
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return read_token(token)


# ============================================================
# RATE LIMITING
# ============================================================

def _login_attempts_col():
    return db.get_db()["login_attempts"]


def record_login_attempt(username, ip, success):
    """Log every login attempt (success or failure)."""
    if not MONGO_OK:
        return
    try:
        _login_attempts_col().insert_one({
            "username": username,
            "ip": ip or "unknown",
            "success": bool(success),
            "ts": datetime.now(timezone.utc),
        })
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        _login_attempts_col().delete_many({"ts": {"$lt": cutoff}})
    except Exception as e:
        print(f"[auth] record_login_attempt failed: {e}")


def is_rate_limited(username, ip):
    """Return (limited: bool, seconds_left: int)."""
    if not MONGO_OK:
        return False, 0
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_WINDOW_MIN)
        query = {
            "$or": [
                {"ip": ip or "unknown"},
                {"username": username or ""}
            ],
            "success": False,
            "ts": {"$gte": cutoff}
        }
        failed = _login_attempts_col().count_documents(query)
        if failed >= RATE_LIMIT_MAX_ATTEMPTS:
            oldest_doc = next(
                iter(_login_attempts_col().find(query).sort("ts", 1).limit(1)),
                None
            )
            if oldest_doc and "ts" in oldest_doc:
                elapsed = (datetime.now(timezone.utc) - oldest_doc["ts"]).total_seconds()
                seconds_left = max(0, RATE_LIMIT_WINDOW_MIN * 60 - int(elapsed))
                return True, seconds_left
            return True, RATE_LIMIT_WINDOW_MIN * 60
        return False, 0
    except Exception as e:
        print(f"[auth] is_rate_limited failed: {e}")
        return False, 0


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
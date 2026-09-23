"""
db.py — MongoDB connection + collections for MIU BEE Generator.

Collections:
    curriculum            courses + topics (mirrors curriculum.json)
    generated_content     AI cache per topic
    slides                pptx metadata
    pdfs                  pdf metadata
    users                 login accounts
    sessions              active login sessions
    reports               email report log
    usage                 AI provider usage
    activity_log          everything that happens
    settings              system config
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "miu_bee")

_client = None
_db = None


def get_client():
    """Return a singleton MongoClient."""
    global _client
    if _client is None:
        if not MONGODB_URI:
            raise RuntimeError(
                "MONGODB_URI is not set. Add it to .env or environment variables."
            )
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=20000,
        )
    return _client


def get_db():
    """Return the miu_bee database."""
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db


def ping():
    """Test connection. Returns (ok, message)."""
    try:
        get_client().admin.command("ping")
        return True, f"Connected to MongoDB · database: {DB_NAME}"
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        return False, f"MongoDB connection failed: {e}"
    except Exception as e:
        return False, f"MongoDB error: {e}"


# ---------------- Collections ----------------

def col_curriculum():
    return get_db()["curriculum"]


def col_content():
    return get_db()["generated_content"]


def col_slides():
    return get_db()["slides"]


def col_pdfs():
    return get_db()["pdfs"]


def col_users():
    return get_db()["users"]


def col_sessions():
    return get_db()["sessions"]


def col_reports():
    return get_db()["reports"]


def col_usage():
    return get_db()["usage"]


def col_activity():
    return get_db()["activity_log"]


def col_settings():
    return get_db()["settings"]


# ---------------- Index setup ----------------

def ensure_indexes():
    """Create indexes used by common queries."""
    # curriculum: unique on code
    col_curriculum().create_index([("code", ASCENDING)], unique=True)
    col_curriculum().create_index([("year", ASCENDING),
                                   ("semester", ASCENDING)])

    # content: one cache per (course_code, topic_number)
    col_content().create_index(
        [("course_code", ASCENDING), ("topic_number", ASCENDING)],
        unique=True
    )
    col_content().create_index([("course_code", ASCENDING)])

    # slides / pdfs
    col_slides().create_index(
        [("course_code", ASCENDING), ("topic_number", ASCENDING)],
        unique=True
    )
    col_pdfs().create_index(
        [("course_code", ASCENDING), ("topic_number", ASCENDING)],
        unique=True
    )

    # users unique email
    col_users().create_index([("email", ASCENDING)], unique=True)

    # sessions expire after 30 days
    col_sessions().create_index([("created_at", ASCENDING)],
                                expireAfterSeconds=60 * 60 * 24 * 30)

    # activity: newest first
    col_activity().create_index([("ts", ASCENDING)])

    # usage: one doc per day
    col_usage().create_index([("date", ASCENDING)], unique=True)


def log_activity(action, detail=None, user=None):
    """Append one line to activity_log."""
    try:
        col_activity().insert_one({
            "ts": datetime.now(timezone.utc),
            "action": action,
            "detail": detail or "",
            "user": user or "system",
        })
    except Exception:
        pass  # never break the app because of logging


def usage_today():
    """Get-or-create today's usage doc."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc = col_usage().find_one({"date": today})
    if not doc:
        doc = {
            "date": today,
            "groq_1_tokens": 0,
            "groq_2_tokens": 0,
            "gemini_requests": 0,
            "mistral_tokens": 0,
            "topics_generated": 0,
        }
        col_usage().insert_one(doc)
    return doc


if __name__ == "__main__":
    ok, msg = ping()
    print(("OK  " if ok else "FAIL  ") + msg)
    if ok:
        ensure_indexes()
        print("Indexes created.")
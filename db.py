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

GridFS bucket:
    fs                    pptx file bytes (survives Render restarts)
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from gridfs import GridFS

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
    col_curriculum().create_index([("code", ASCENDING)], unique=True)
    col_curriculum().create_index([("year", ASCENDING),
                                   ("semester", ASCENDING)])

    col_content().create_index(
        [("course_code", ASCENDING), ("topic_number", ASCENDING)],
        unique=True
    )
    col_content().create_index([("course_code", ASCENDING)])

    col_slides().create_index(
        [("course_code", ASCENDING), ("topic_number", ASCENDING)],
        unique=True
    )
    col_pdfs().create_index(
        [("course_code", ASCENDING), ("topic_number", ASCENDING)],
        unique=True
    )

    col_users().create_index([("email", ASCENDING)], unique=True)

    col_sessions().create_index([("created_at", ASCENDING)],
                                expireAfterSeconds=60 * 60 * 24 * 30)

    col_activity().create_index([("ts", ASCENDING)])

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
        pass


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


# ============================================================
# GRIDFS — store pptx files INSIDE MongoDB
# ============================================================

def get_fs():
    """Return a GridFS bucket for storing files."""
    return GridFS(get_db())


def save_pptx_to_mongo(course_code, topic_number, filename, filepath):
    """
    Save a pptx file to MongoDB GridFS.
    Deletes any previous version with the same (course_code, topic_number).
    Returns the GridFS file id (str) or None on failure.
    """
    try:
        fs = get_fs()

        # Delete any previous version with the same key
        for old in fs.find({"course_code": course_code, "topic_number": topic_number}):
            fs.delete(old._id)

        # Save new version
        with open(filepath, "rb") as f:
            file_id = fs.put(
                f,
                filename=filename,
                course_code=course_code,
                topic_number=topic_number,
                content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                uploaded_at=datetime.now(timezone.utc),
            )
        return str(file_id)
    except Exception as e:
        print(f"[gridfs] save failed for {course_code}/{topic_number}: {e}")
        return None


def get_pptx_from_mongo(course_code, topic_number):
    """
    Fetch a pptx from MongoDB GridFS.
    Returns (bytes, filename) or (None, None) if not found.
    """
    try:
        fs = get_fs()
        grid_out = fs.find_one(
            {"course_code": course_code, "topic_number": topic_number}
        )
        if not grid_out:
            return None, None
        return grid_out.read(), grid_out.filename
    except Exception as e:
        print(f"[gridfs] get failed: {e}")
        return None, None


def pptx_exists_in_mongo(course_code, topic_number):
    """Check if a pptx is stored in MongoDB."""
    try:
        fs = get_fs()
        doc = fs.find_one(
            {"course_code": course_code, "topic_number": topic_number},
            {"_id": 1}
        )
        return doc is not None
    except Exception:
        return False


def list_pptx_in_mongo():
    """Return metadata for all pptx files in MongoDB (without the bytes)."""
    try:
        fs = get_fs()
        out = []
        for f in fs.find({}):
            doc = {
                "filename": f.filename,
                "course_code": getattr(f, "course_code", None),
                "topic_number": getattr(f, "topic_number", None),
                "length": f.length,
            }
            if hasattr(f, "uploaded_at") and f.uploaded_at:
                if hasattr(f.uploaded_at, "isoformat"):
                    doc["uploaded_at"] = f.uploaded_at.isoformat()
                else:
                    doc["uploaded_at"] = str(f.uploaded_at)
            out.append(doc)
        return out
    except Exception as e:
        print(f"[gridfs] list failed: {e}")
        return []


if __name__ == "__main__":
    ok, msg = ping()
    print(("OK  " if ok else "FAIL  ") + msg)
    if ok:
        ensure_indexes()
        print("Indexes created.")
        print(f"GridFS files: {len(list_pptx_in_mongo())}")
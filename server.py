"""
server.py — Flask API for the MIU BEE React frontend.
Endpoints:
  GET  /api/stats              → overall stats + per-course rows
  GET  /api/logs?since=N       → new log lines
  GET  /api/tree               → nested file tree
  POST /api/run/<task>         → start a script
  POST /api/stop               → stop current run
  POST /api/report/email       → send report email now
  GET  /download/<kind>/<path> → download pptx/pdf
  GET  /api/db/status          → MongoDB connection status
  GET  /api/search?q=...       → search topics in MongoDB
  GET  /api/dashboard          → stats + charts data
  GET  /api/zip/all            → download all slides as zip
  GET  /api/zip/course/<code>  → download one course as zip
  POST /api/login              → login (rate-limited)
  POST /api/logout             → logout
  GET  /api/me                 → current user info + permissions
  POST /api/me/password        → change own password
  GET  /api/me/logins          → recent login attempts
  GET/POST/PATCH/DELETE /api/users  → admin user management
  GET  /                       → serves React build if present
"""

import io
import json
import subprocess
import threading
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from flask import (
    Flask, jsonify, request, send_from_directory, send_file, make_response
)
from flask_cors import CORS

import mailer

try:
    import db
    MONGO_AVAILABLE = True
except Exception as e:
    print(f"[db] MongoDB not available: {e}")
    MONGO_AVAILABLE = False

import auth

BASE = Path(__file__).parent
CURRICULUM = BASE / "curriculum.json"
CACHE_ROOT = BASE / "generated_content"
SLIDES_ROOT = BASE / "output_slides"
PDFS_ROOT = BASE / "output_pdfs"
FRONTEND_DIST = BASE / "frontend" / "dist"
VENV_PY = BASE / ".venv" / "Scripts" / "python.exe"

app = Flask(__name__, static_folder=None)
CORS(app, supports_credentials=True)

# Create the default admin user on startup
try:
    auth.create_default_admin()
except Exception as e:
    print(f"[auth] startup hook failed: {e}")

# Start background scheduler (only if AUTO_GENERATE=true)
try:
    import scheduler
    scheduler.start()
except Exception as e:
    print(f"[scheduler] startup failed: {e}")


def python_exe():
    if VENV_PY.exists():
        return str(VENV_PY)
    return sys.executable


def clean_name(text):
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")


class State:
    def __init__(self):
        self.proc = None
        self.log = []
        self.max_log = 5000
        self.lock = threading.Lock()
        self.task = None
        self.auto_report_sent = False

state = State()


def push(line):
    with state.lock:
        state.log.append(line)
        if len(state.log) > state.max_log:
            state.log = state.log[-state.max_log:]


def run_script(script_name, args=None, label=None):
    if state.proc and state.proc.poll() is None:
        return False, "A script is already running."

    script = BASE / script_name
    if not script.exists():
        return False, f"Script not found: {script_name}"

    cmd = [python_exe(), str(script)] + (args or [])
    state.task = label or script_name
    state.auto_report_sent = False
    push(f"\n$ {' '.join(cmd)}\n" + "=" * 60 + "\n")

    def worker():
        try:
            state.proc = subprocess.Popen(
                cmd, cwd=str(BASE),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)
            )
            for line in state.proc.stdout:
                push(line)
            state.proc.wait()
            push(f"\n[exit code {state.proc.returncode}]\n")

            if not state.auto_report_sent and script_name == "gen_topic.py":
                state.auto_report_sent = True
                push("\n[mailer] Sending auto progress report...\n")
                ok, msg = mailer.send_report("Auto Progress Report")
                push(f"[mailer] {'OK' if ok else 'FAIL'} {msg}\n")
        except Exception as e:
            push(f"\n[ERROR] {e}\n")
        finally:
            state.proc = None
            state.task = None

    threading.Thread(target=worker, daemon=True).start()
    return True, "Started"


def scan_stats():
    if not CURRICULUM.exists():
        return {"total": 0, "done": 0, "remaining": 0, "pptx": 0, "pdf": 0,
                "courses": [], "running": False, "task": None, "pct": 0}

    with open(CURRICULUM, "r", encoding="utf-8") as f:
        data = json.load(f)

    courses = []
    total = done = 0
    for program in data["programs"]:
        pc = program["code"]
        for yb in program["years"]:
            y = yb["year"]
            for sb in yb["semesters"]:
                s = sb["semester"]
                for course in sb["courses"]:
                    cdir = f"{clean_name(course['code'])}_{clean_name(course['name'])}"
                    topics = course.get("topics", [])
                    c_done = 0
                    for idx, topic in enumerate(topics, 1):
                        stem = f"{idx:02d}_{clean_name(topic)}"
                        if (CACHE_ROOT / pc / f"Year_{y}" / f"Semester_{s}"
                                / cdir / f"{stem}.json").exists():
                            c_done += 1
                    courses.append({
                        "code": course["code"],
                        "name": course["name"],
                        "year": y,
                        "semester": s,
                        "total": len(topics),
                        "done": c_done
                    })
                    total += len(topics)
                    done += c_done

    pptx = len(list(SLIDES_ROOT.rglob("*.pptx"))) if SLIDES_ROOT.exists() else 0
    pdf = len(list(PDFS_ROOT.rglob("*.pdf"))) if PDFS_ROOT.exists() else 0

    return {
        "total": total,
        "done": done,
        "remaining": total - done,
        "pptx": pptx,
        "pdf": pdf,
        "pct": round(done / total * 100, 1) if total else 0,
        "courses": courses,
        "running": bool(state.proc and state.proc.poll() is None),
        "task": state.task
    }


def build_tree(root, rel=""):
    if not root.exists():
        return {"name": root.name, "type": "folder", "children": []}
    node = {"name": root.name, "type": "folder", "children": []}
    for entry in sorted(root.iterdir()):
        rel_child = f"{rel}/{entry.name}" if rel else entry.name
        if entry.is_dir():
            node["children"].append(build_tree(entry, rel_child))
        else:
            node["children"].append({
                "name": entry.name,
                "type": "file",
                "size": entry.stat().st_size,
                "path": rel_child
            })
    return node


# ============ Auth routes (public) ============

@app.route("/api/login", methods=["POST"])
def api_login():
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or ""

    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password required"}), 400

    # --- Rate limit check ---
    limited, seconds_left = auth.is_rate_limited(username, ip)
    if limited:
        mins = (seconds_left + 59) // 60
        return jsonify({
            "ok": False,
            "error": f"Too many failed attempts. Try again in {mins} minute(s)."
        }), 429

    user = auth.find_user(username)
    ok = bool(user) and auth.verify_password(password, user.get("password_hash", ""))

    # --- Log every attempt ---
    auth.record_login_attempt(username, ip, ok)

    if not ok:
        if MONGO_AVAILABLE:
            try:
                db.log_activity("login_failed", f"user={username} ip={ip}")
            except Exception:
                pass
        return jsonify({"ok": False, "error": "Invalid credentials"}), 401

    role = user.get("role", "viewer")
    if MONGO_AVAILABLE:
        try:
            db.log_activity("login_success", f"user={username} ip={ip}")
        except Exception:
            pass

    resp = make_response(jsonify({
        "ok": True,
        "user": {
            "username": user["username"],
            "role": role,
            "email": user.get("email", ""),
            "permissions": sorted(auth.ROLE_PERMISSIONS.get(role, set())),
        }
    }))
    return auth.set_session_cookie(resp, user["username"])


@app.route("/api/logout", methods=["POST"])
def api_logout():
    resp = make_response(jsonify({"ok": True}))
    return auth.clear_session_cookie(resp)


@app.route("/api/me")
def api_me():
    user = auth.current_user()
    if not user:
        return jsonify({"ok": False, "authenticated": False}), 200
    doc = auth.find_user(user) or {}
    role = doc.get("role", "viewer")
    return jsonify({
        "ok": True,
        "authenticated": True,
        "user": {
            "username": user,
            "role": role,
            "email": doc.get("email", ""),
            "permissions": sorted(auth.ROLE_PERMISSIONS.get(role, set())),
        }
    })


@app.route("/api/me/password", methods=["POST"])
@auth.require_auth
def api_me_password():
    """Change the current user's own password."""
    body = request.get_json(silent=True) or {}
    old_password = body.get("old_password") or ""
    new_password = body.get("new_password") or ""
    me = auth.current_user()

    ok, msg = auth.change_own_password(me, old_password, new_password)

    if MONGO_AVAILABLE:
        try:
            db.log_activity(
                "password_changed" if ok else "password_change_failed",
                f"user={me}",
                user=me
            )
        except Exception:
            pass

    return jsonify({"ok": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/me/logins", methods=["GET"])
@auth.require_auth
def api_me_logins():
    """Return recent login attempts for the current user."""
    if not MONGO_AVAILABLE:
        return jsonify({"ok": True, "logins": []})
    me = auth.current_user()
    try:
        docs = list(db.get_db()["login_attempts"]
                    .find({"username": me}, {"_id": 0})
                    .sort("ts", -1).limit(20))
        for d in docs:
            if "ts" in d and hasattr(d["ts"], "isoformat"):
                d["ts"] = d["ts"].isoformat()
        return jsonify({"ok": True, "logins": docs})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ============ Protected routes ============

@app.route("/api/stats")
@auth.require_auth
def api_stats():
    return jsonify(scan_stats())


@app.route("/api/logs")
@auth.require_auth
def api_logs():
    since = int(request.args.get("since", 0))
    with state.lock:
        lines = state.log[since:]
        nxt = len(state.log)
    return jsonify({"lines": lines, "next": nxt})


@app.route("/api/tree")
@auth.require_auth
def api_tree():
    kind = request.args.get("kind", "pptx")
    root = SLIDES_ROOT if kind == "pptx" else PDFS_ROOT if kind == "pdf" else CACHE_ROOT
    return jsonify(build_tree(root))


@app.route("/api/run/<task>", methods=["POST"])
@auth.require_auth
def api_run(task):
    tasks = {
        "generate":      ("gen_topic.py",             None,               "Generating slides",     "generate"),
        "progress":      ("check_progress.py",        None,               "Checking progress",     "progress"),
        "pdf":           ("convert_to_pdf.py",        ["--skip-existing"], "Converting to PDF",     "pdf"),
        "rebuild":       ("regenerate_from_cache.py", None,               "Rebuilding from cache", "rebuild"),
        "cleanup":       ("cleanup.py",               None,               "Cleanup (dry run)",     "cleanup"),
        "cleanup-apply": ("cleanup.py",               ["--apply"],         "Cleanup (apply)",       "cleanup_apply"),
        "migrate":       ("migrate_to_mongo.py",      None,               "Migrating to MongoDB",  "manage_users"),
    }
    if task not in tasks:
        return jsonify({"ok": False, "error": f"Unknown task {task}"}), 400

    script, args, label, permission = tasks[task]
    user = auth.current_user()
    if not auth.has_permission(user, permission):
        return jsonify({
            "ok": False,
            "error": f"Your role ({auth.user_role(user)}) cannot run '{task}'"
        }), 403

    ok, msg = run_script(script, args, label)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/stop", methods=["POST"])
@auth.require_permission("stop")
def api_stop():
    if state.proc and state.proc.poll() is None:
        state.proc.terminate()
        push("\n[STOPPED]\n")
        return jsonify({"ok": True})
    return jsonify({"ok": False})


@app.route("/api/report/email", methods=["POST"])
@auth.require_permission("report")
def api_report_email():
    body = request.get_json(silent=True) or {}
    label = body.get("label", "Manual Report")
    ok, msg = mailer.send_report(label)
    return jsonify({"ok": ok, "message": msg})


@app.route("/download/<kind>/<path:filepath>")
@auth.require_auth
def download(kind, filepath):
    root = SLIDES_ROOT if kind == "pptx" else PDFS_ROOT
    target = (root / filepath).resolve()
    if not str(target).startswith(str(root.resolve())) or not target.exists():
        return "Not found", 404
    return send_file(target, as_attachment=True)


# ---------------- MongoDB routes ----------------

@app.route("/api/db/status")
@auth.require_role("admin")
def api_db_status():
    if not MONGO_AVAILABLE:
        return jsonify({"ok": False, "message": "MongoDB module not loaded"})
    ok, msg = db.ping()
    counts = {}
    if ok:
        try:
            counts = {
                "curriculum": db.col_curriculum().count_documents({}),
                "content": db.col_content().count_documents({}),
                "slides": db.col_slides().count_documents({}),
                "users": db.col_users().count_documents({}),
                "activity": db.col_activity().count_documents({}),
            }
        except Exception as e:
            counts = {"error": str(e)}
    return jsonify({"ok": ok, "message": msg, "counts": counts})


@app.route("/api/search")
@auth.require_permission("search")
def api_search():
    if not MONGO_AVAILABLE:
        return jsonify({"ok": False, "error": "MongoDB not available"}), 503

    q = (request.args.get("q") or "").strip()
    limit = min(int(request.args.get("limit", 50)), 200)

    if not q:
        return jsonify({"ok": True, "results": [], "count": 0})

    import re
    pattern = re.compile(re.escape(q), re.IGNORECASE)

    course_results = list(db.col_curriculum().find(
        {"$or": [{"name": pattern}, {"topics": pattern}, {"code": pattern}]},
        {"_id": 0}
    ).limit(limit))

    content_results = list(db.col_content().find(
        {"$or": [{"topic": pattern}, {"course_name": pattern}, {"course_code": pattern}]},
        {"_id": 0, "content": 0}
    ).limit(limit))

    return jsonify({
        "ok": True,
        "query": q,
        "courses": course_results,
        "topics": content_results,
        "count": len(course_results) + len(content_results)
    })


@app.route("/api/dashboard")
@auth.require_permission("dashboard")
def api_dashboard():
    stats = scan_stats()

    if not MONGO_AVAILABLE:
        return jsonify({"ok": True, "stats": stats, "charts": {}})

    charts = {}

    try:
        from datetime import datetime, timezone, timedelta
        days = []
        now = datetime.now(timezone.utc)
        for i in range(13, -1, -1):
            d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            cnt = db.col_content().count_documents({
                "updated_at": {"$gte": now - timedelta(days=i + 1),
                               "$lt": now - timedelta(days=i)}
            })
            days.append({"date": d, "count": cnt})
        charts["daily"] = days
    except Exception as e:
        charts["daily_error"] = str(e)

    try:
        pipeline = [
            {"$group": {"_id": "$year", "total": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        by_year = list(db.col_content().aggregate(pipeline))
        charts["by_year"] = [{"year": r["_id"], "count": r["total"]} for r in by_year]
    except Exception as e:
        charts["by_year_error"] = str(e)

    try:
        recent = list(db.col_activity().find({}, {"_id": 0})
                      .sort("ts", -1).limit(20))
        for r in recent:
            if "ts" in r and hasattr(r["ts"], "isoformat"):
                r["ts"] = r["ts"].isoformat()
        charts["recent"] = recent
    except Exception as e:
        charts["recent_error"] = str(e)

    return jsonify({"ok": True, "stats": stats, "charts": charts})


@app.route("/api/zip/all")
@auth.require_auth
def api_zip_all():
    if not SLIDES_ROOT.exists():
        return "No slides found", 404

    pptx_files = list(SLIDES_ROOT.rglob("*.pptx"))
    if not pptx_files:
        return "No slides found", 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in pptx_files:
            arcname = str(f.relative_to(SLIDES_ROOT))
            zf.write(f, arcname)
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name="miu_bee_slides.zip"
    )


@app.route("/api/zip/course/<course_code>")
@auth.require_auth
def api_zip_course(course_code):
    if not SLIDES_ROOT.exists():
        return "No slides found", 404

    needle = course_code.replace(" ", "_")
    pptx_files = [f for f in SLIDES_ROOT.rglob("*.pptx")
                  if needle in str(f.parent)]
    if not pptx_files:
        return f"No slides found for {course_code}", 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in pptx_files:
            arcname = str(f.relative_to(SLIDES_ROOT))
            zf.write(f, arcname)
    buf.seek(0)

    safe = course_code.replace(" ", "_")
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{safe}_slides.zip"
    )


# ---------------- User management (admin only) ----------------

@app.route("/api/users", methods=["GET"])
@auth.require_role("admin")
def api_users_list():
    if not MONGO_AVAILABLE:
        return jsonify({"ok": False, "error": "MongoDB not available"}), 503
    try:
        users = list(db.col_users().find(
            {},
            {"_id": 0, "password_hash": 0}
        ).sort("username", 1))
        for u in users:
            if "created_at" in u and hasattr(u["created_at"], "isoformat"):
                u["created_at"] = u["created_at"].isoformat()
        return jsonify({"ok": True, "users": users})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/users", methods=["POST"])
@auth.require_role("admin")
def api_users_create():
    if not MONGO_AVAILABLE:
        return jsonify({"ok": False, "error": "MongoDB not available"}), 503
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    email = (body.get("email") or "").strip()
    role = (body.get("role") or "viewer").lower()

    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password required"}), 400
    if role not in ("admin", "lecturer", "viewer"):
        return jsonify({"ok": False, "error": "Invalid role"}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "Password must be at least 6 characters"}), 400

    if auth.find_user(username):
        return jsonify({"ok": False, "error": "Username already exists"}), 409

    try:
        db.col_users().insert_one({
            "username": username,
            "email": email,
            "password_hash": auth.hash_password(password),
            "role": role,
            "created_at": datetime.now(timezone.utc),
        })
        db.log_activity("user_created", f"user={username} role={role}",
                        user=auth.current_user())
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/users/<username>", methods=["PATCH"])
@auth.require_role("admin")
def api_users_update(username):
    if not MONGO_AVAILABLE:
        return jsonify({"ok": False, "error": "MongoDB not available"}), 503
    body = request.get_json(silent=True) or {}
    updates = {}

    if "role" in body:
        role = (body["role"] or "").lower()
        if role not in ("admin", "lecturer", "viewer"):
            return jsonify({"ok": False, "error": "Invalid role"}), 400
        updates["role"] = role

    if "email" in body:
        updates["email"] = (body["email"] or "").strip()

    if "password" in body and body["password"]:
        if len(body["password"]) < 6:
            return jsonify({"ok": False, "error": "Password too short"}), 400
        updates["password_hash"] = auth.hash_password(body["password"])

    if not updates:
        return jsonify({"ok": False, "error": "Nothing to update"}), 400

    try:
        res = db.col_users().update_one({"username": username}, {"$set": updates})
        if res.matched_count == 0:
            return jsonify({"ok": False, "error": "User not found"}), 404
        db.log_activity("user_updated", f"user={username} fields={list(updates)}",
                        user=auth.current_user())
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/users/<username>", methods=["DELETE"])
@auth.require_role("admin")
def api_users_delete(username):
    if not MONGO_AVAILABLE:
        return jsonify({"ok": False, "error": "MongoDB not available"}), 503

    me = auth.current_user()
    if username == me:
        return jsonify({"ok": False, "error": "Cannot delete your own account"}), 400

    try:
        res = db.col_users().delete_one({"username": username})
        if res.deleted_count == 0:
            return jsonify({"ok": False, "error": "User not found"}), 404
        db.log_activity("user_deleted", f"user={username}", user=me)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/users/<username>/password", methods=["POST"])
@auth.require_role("admin")
def api_users_password(username):
    if not MONGO_AVAILABLE:
        return jsonify({"ok": False, "error": "MongoDB not available"}), 503
    body = request.get_json(silent=True) or {}
    new_password = body.get("password") or ""
    if len(new_password) < 6:
        return jsonify({"ok": False, "error": "Password must be at least 6 characters"}), 400
    try:
        res = db.col_users().update_one(
            {"username": username},
            {"$set": {"password_hash": auth.hash_password(new_password)}}
        )
        if res.matched_count == 0:
            return jsonify({"ok": False, "error": "User not found"}), 404
        db.log_activity("password_reset", f"user={username}",
                        user=auth.current_user())
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---- Serve React build ----
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if not FRONTEND_DIST.exists():
        return ("<h1>Frontend not built</h1>"
                "<p>Run: cd frontend && npm install && npm run dev</p>"), 200
    target = FRONTEND_DIST / path
    if path and target.exists() and target.is_file():
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("  MIU BEE API server")
    print(f"  -> http://localhost:{port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
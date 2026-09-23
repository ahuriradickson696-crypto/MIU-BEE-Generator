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
  GET  /                       → serves React build if present
"""

import json
import subprocess
import threading
import sys
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS

import mailer

BASE = Path(__file__).parent
CURRICULUM = BASE / "curriculum.json"
CACHE_ROOT = BASE / "generated_content"
SLIDES_ROOT = BASE / "output_slides"
PDFS_ROOT = BASE / "output_pdfs"
FRONTEND_DIST = BASE / "frontend" / "dist"
VENV_PY = BASE / ".venv" / "Scripts" / "python.exe"

app = Flask(__name__, static_folder=None)
CORS(app)


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

            # Auto email report if generation just finished
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
    """Return nested dict tree of files under root."""
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


# ---------------- Routes ----------------

@app.route("/api/stats")
def api_stats():
    return jsonify(scan_stats())


@app.route("/api/logs")
def api_logs():
    since = int(request.args.get("since", 0))
    with state.lock:
        lines = state.log[since:]
        nxt = len(state.log)
    return jsonify({"lines": lines, "next": nxt})


@app.route("/api/tree")
def api_tree():
    kind = request.args.get("kind", "pptx")
    root = SLIDES_ROOT if kind == "pptx" else PDFS_ROOT if kind == "pdf" else CACHE_ROOT
    return jsonify(build_tree(root))


@app.route("/api/run/<task>", methods=["POST"])
def api_run(task):
    tasks = {
        "generate": ("gen_topic.py", None, "Generating slides"),
        "progress": ("check_progress.py", None, "Checking progress"),
        "pdf": ("convert_to_pdf.py", ["--skip-existing"], "Converting to PDF"),
        "rebuild": ("regenerate_from_cache.py", None, "Rebuilding from cache"),
        "cleanup": ("cleanup.py", None, "Cleanup (dry run)"),
        "cleanup-apply": ("cleanup.py", ["--apply"], "Cleanup (apply)"),
    }
    if task not in tasks:
        return jsonify({"ok": False, "error": f"Unknown task {task}"}), 400
    script, args, label = tasks[task]
    ok, msg = run_script(script, args, label)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    if state.proc and state.proc.poll() is None:
        state.proc.terminate()
        push("\n[STOPPED]\n")
        return jsonify({"ok": True})
    return jsonify({"ok": False})


@app.route("/api/report/email", methods=["POST"])
def api_report_email():
    body = request.get_json(silent=True) or {}
    label = body.get("label", "Manual Report")
    ok, msg = mailer.send_report(label)
    return jsonify({"ok": ok, "message": msg})


@app.route("/download/<kind>/<path:filepath>")
def download(kind, filepath):
    root = SLIDES_ROOT if kind == "pptx" else PDFS_ROOT
    target = (root / filepath).resolve()
    if not str(target).startswith(str(root.resolve())) or not target.exists():
        return "Not found", 404
    return send_file(target, as_attachment=True)


# ---- Serve React build (after `npm run build`) ----
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
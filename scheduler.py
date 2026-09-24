"""
scheduler.py - automatic nightly generation.
Runs gen_topic.py at 02:00 UTC every day.
Config via env vars:
  AUTO_GENERATE=true       (default: false)
  AUTO_HOUR_UTC=2          (default: 2)
"""

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

BASE = Path(__file__).parent
VENV_PY = BASE / ".venv" / "Scripts" / "python.exe"
GEN_SCRIPT = BASE / "gen_topic.py"

AUTO_ENABLED = os.getenv("AUTO_GENERATE", "false").lower() == "true"
AUTO_HOUR = int(os.getenv("AUTO_HOUR_UTC", "2"))

_scheduler = None


def _python():
    if VENV_PY.exists():
        return str(VENV_PY)
    return sys.executable


def run_generation():
    print(f"[scheduler] Auto-generation at {datetime.now(timezone.utc).isoformat()}")
    try:
        result = subprocess.run(
            [_python(), str(GEN_SCRIPT)],
            cwd=str(BASE),
            capture_output=True,
            text=True,
            timeout=60 * 60 * 4,
        )
        print(f"[scheduler] Exit code: {result.returncode}")
        if result.stdout:
            print(result.stdout[-2000:])
    except subprocess.TimeoutExpired:
        print("[scheduler] Generation timed out")
    except Exception as e:
        print(f"[scheduler] Error: {e}")


def start():
    global _scheduler
    if not AUTO_ENABLED:
        print("[scheduler] Auto-generation OFF (set AUTO_GENERATE=true to enable)")
        return None
    if _scheduler:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        run_generation,
        "cron",
        hour=AUTO_HOUR,
        minute=0,
        id="nightly_generation",
        replace_existing=True,
    )
    _scheduler.start()
    print(f"[scheduler] Started - nightly generation at {AUTO_HOUR:02d}:00 UTC")
    return _scheduler
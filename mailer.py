"""
mailer.py
Sends automatic email reports of generator progress to REPORT_TO.
Uses SMTP via Gmail App Password (config in .env).
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
REPORT_TO = os.getenv("REPORT_TO", "ahuriratech@gmail.com")

BASE = Path(__file__).parent
CACHE_ROOT = BASE / "generated_content"
SLIDES_ROOT = BASE / "output_slides"
PDFS_ROOT = BASE / "output_pdfs"
CURRICULUM = BASE / "curriculum.json"


def _clean(text):
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")


def collect_stats():
    if not CURRICULUM.exists():
        return None

    with open(CURRICULUM, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    total = done = 0

    for program in data["programs"]:
        pc = program["code"]
        for yb in program["years"]:
            y = yb["year"]
            for sb in yb["semesters"]:
                s = sb["semester"]
                for course in sb["courses"]:
                    cdir = f"{_clean(course['code'])}_{_clean(course['name'])}"
                    topics = course.get("topics", [])
                    t_count = len(topics)
                    c_done = 0
                    for idx, topic in enumerate(topics, 1):
                        stem = f"{idx:02d}_{_clean(topic)}"
                        if (CACHE_ROOT / pc / f"Year_{y}" / f"Semester_{s}"
                                / cdir / f"{stem}.json").exists():
                            c_done += 1
                    rows.append({
                        "code": course["code"],
                        "name": course["name"],
                        "year": y,
                        "semester": s,
                        "done": c_done,
                        "total": t_count
                    })
                    total += t_count
                    done += c_done

    pptx = len(list(SLIDES_ROOT.rglob("*.pptx"))) if SLIDES_ROOT.exists() else 0
    pdf = len(list(PDFS_ROOT.rglob("*.pdf"))) if PDFS_ROOT.exists() else 0

    return {
        "rows": rows,
        "total": total,
        "done": done,
        "remaining": total - done,
        "pptx": pptx,
        "pdf": pdf,
        "pct": round(done / total * 100, 1) if total else 0
    }


def build_html(stats):
    ts = datetime.now().strftime("%A, %d %B %Y at %H:%M")
    pct = stats["pct"]

    rows_html = ""
    last_key = None
    for r in stats["rows"]:
        key = f"Y{r['year']}S{r['semester']}"
        if key != last_key:
            rows_html += (
                f'<tr><td colspan="4" style="background:#E8F5EE;padding:8px;'
                f'font-weight:700;color:#00823C;">'
                f'Year {r["year"]} - Semester {r["semester"]}</td></tr>'
            )
            last_key = key
        pct_row = round(r["done"] / r["total"] * 100) if r["total"] else 0
        color = "#00823C" if pct_row == 100 else "#E8A93C" if pct_row > 0 else "#C81E28"
        rows_html += (
            f'<tr>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #EEE;">{r["code"]}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #EEE;">{r["name"]}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #EEE;text-align:center;'
            f'color:{color};font-weight:600;">{r["done"]} / {r["total"]}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #EEE;text-align:right;">'
            f'{pct_row}%</td>'
            f'</tr>'
        )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Segoe UI,Arial,sans-serif;background:#F4F6F8;margin:0;padding:20px;">
  <div style="max-width:820px;margin:0 auto;background:white;border-radius:12px;
              overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.08);">
    <div style="background:linear-gradient(135deg,#00823C,#006B31);color:white;padding:26px 32px;">
      <div style="font-size:22px;font-weight:700;">MIU BEE - Progress Report</div>
      <div style="font-size:13px;opacity:.9;margin-top:4px;">
        Metropolitan International University - Bachelor of Science in Electrical Engineering
      </div>
    </div>
    <div style="padding:26px 32px;">
      <p style="margin:0 0 18px 0;color:#666;font-size:13px;">{ts}</p>
      <div style="display:flex;gap:14px;margin-bottom:24px;flex-wrap:wrap;">
        <div style="flex:1;min-width:120px;background:#F4F6F8;border-left:4px solid #00823C;padding:14px 18px;border-radius:6px;">
          <div style="font-size:11px;color:#666;text-transform:uppercase;">Topics</div>
          <div style="font-size:24px;font-weight:700;color:#00823C;">{stats['total']}</div>
        </div>
        <div style="flex:1;min-width:120px;background:#F4F6F8;border-left:4px solid #00823C;padding:14px 18px;border-radius:6px;">
          <div style="font-size:11px;color:#666;text-transform:uppercase;">Completed</div>
          <div style="font-size:24px;font-weight:700;color:#00823C;">{stats['done']}</div>
        </div>
        <div style="flex:1;min-width:120px;background:#F4F6F8;border-left:4px solid #C81E28;padding:14px 18px;border-radius:6px;">
          <div style="font-size:11px;color:#666;text-transform:uppercase;">Remaining</div>
          <div style="font-size:24px;font-weight:700;color:#C81E28;">{stats['remaining']}</div>
        </div>
        <div style="flex:1;min-width:120px;background:#F4F6F8;border-left:4px solid #555;padding:14px 18px;border-radius:6px;">
          <div style="font-size:11px;color:#666;text-transform:uppercase;">Files</div>
          <div style="font-size:24px;font-weight:700;color:#555;">{stats['pptx']} pptx / {stats['pdf']} pdf</div>
        </div>
      </div>
      <div style="background:#F4F6F8;border-radius:8px;padding:16px;margin-bottom:24px;">
        <div style="font-size:13px;color:#666;margin-bottom:8px;">Overall progress</div>
        <div style="font-size:26px;font-weight:700;color:#00823C;">{pct}%</div>
      </div>
      <h3 style="color:#00823C;font-size:14px;margin:0 0 10px 0;text-transform:uppercase;">
        Breakdown by Course
      </h3>
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="background:#00823C;color:white;">
            <th style="padding:10px 8px;text-align:left;">Code</th>
            <th style="padding:10px 8px;text-align:left;">Course</th>
            <th style="padding:10px 8px;text-align:center;">Done</th>
            <th style="padding:10px 8px;text-align:right;">Progress</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
      <p style="margin-top:24px;font-size:12px;color:#888;text-align:center;">
        Auto-generated by MIU BEE Slide Generator
      </p>
    </div>
  </div>
</body></html>"""


def send_report(subject_prefix="Progress Report"):
    if not SMTP_USER or not SMTP_PASS:
        return False, "SMTP_USER or SMTP_PASS not set in .env"

    stats = collect_stats()
    if stats is None:
        return False, "curriculum.json not found"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"[MIU BEE] {subject_prefix} - {stats['done']}/{stats['total']} topics ({stats['pct']}%) - {ts}"
    html = build_html(stats)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = REPORT_TO
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [REPORT_TO], msg.as_string())
        return True, f"Report sent to {REPORT_TO}"
    except Exception as e:
        return False, f"SMTP error: {e}"


if __name__ == "__main__":
    ok, msg = send_report("Manual Test Report")
    print(("OK  " if ok else "FAIL  ") + msg)
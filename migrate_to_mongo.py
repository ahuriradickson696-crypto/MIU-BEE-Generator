"""
migrate_to_mongo.py
Upload curriculum.json + local generated_content cache into MongoDB.

Safe to re-run — uses upserts, so nothing is duplicated.

Usage:
    python migrate_to_mongo.py
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

import db

BASE = Path(__file__).parent
CURRICULUM_FILE = BASE / "curriculum.json"
CACHE_ROOT = BASE / "generated_content"


def clean_name(text):
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")


def migrate_curriculum():
    if not CURRICULUM_FILE.exists():
        print("❌ curriculum.json not found")
        return 0

    with open(CURRICULUM_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for program in data["programs"]:
        pc = program["code"]
        for yb in program["years"]:
            y = yb["year"]
            for sb in yb["semesters"]:
                s = sb["semester"]
                for course in sb["courses"]:
                    doc = {
                        "program": pc,
                        "year": y,
                        "semester": s,
                        "code": course["code"],
                        "name": course["name"],
                        "topics": course.get("topics", []),
                        "updated_at": datetime.now(timezone.utc),
                    }
                    db.col_curriculum().update_one(
                        {"code": course["code"]},
                        {"$set": doc},
                        upsert=True,
                    )
                    count += 1

    print(f"✅ Migrated {count} courses to MongoDB")
    return count


def migrate_cache():
    if not CACHE_ROOT.exists():
        print("ℹ️  No local cache to migrate")
        return 0

    count = 0
    for cache_file in sorted(CACHE_ROOT.rglob("*.json")):
        try:
            rel = cache_file.relative_to(CACHE_ROOT)
            parts = rel.parts
            # expected: BEE/Year_X/Semester_Y/Course_Folder/NN_Topic.json
            if len(parts) < 5:
                continue
            program = parts[0]
            year = int(parts[1].replace("Year_", ""))
            semester = int(parts[2].replace("Semester_", ""))
            course_folder = parts[3]
            topic_stem = Path(parts[4]).stem

            cf_parts = course_folder.split("_", 2)
            if len(cf_parts) < 3:
                continue
            course_code = f"{cf_parts[0]} {cf_parts[1]}"
            course_name = cf_parts[2].replace("_", " ")

            if "_" not in topic_stem:
                continue
            num_str, topic_name = topic_stem.split("_", 1)
            try:
                topic_number = int(num_str)
            except ValueError:
                continue
            topic = topic_name.replace("_", " ")

            with open(cache_file, "r", encoding="utf-8") as f:
                content = json.load(f)

            doc = {
                "program": program,
                "year": year,
                "semester": semester,
                "course_code": course_code,
                "course_name": course_name,
                "topic_number": topic_number,
                "topic": topic,
                "content": content,
                "updated_at": datetime.now(timezone.utc),
            }
            db.col_content().update_one(
                {"course_code": course_code, "topic_number": topic_number},
                {"$set": doc},
                upsert=True,
            )
            count += 1
        except Exception as e:
            print(f"  ⚠️  {cache_file.name}: {e}")

    print(f"✅ Migrated {count} cached topics to MongoDB")
    return count


def main():
    print("=" * 60)
    print("  Migrate to MongoDB")
    print("=" * 60)

    ok, msg = db.ping()
    print(("✅ " if ok else "❌ ") + msg)
    if not ok:
        sys.exit(1)

    print("\nCreating indexes...")
    db.ensure_indexes()

    print("\nMigrating curriculum...")
    migrate_curriculum()

    print("\nMigrating local cache...")
    migrate_cache()

    print("\n" + "=" * 60)
    print("  Migration complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
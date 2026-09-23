"""
regenerate_from_cache.py
Rebuild .pptx files from the JSON cache — WITHOUT calling any AI.
Free, instant, unlimited use.

Walks the MIU nested tree:
    generated_content\BEE\Year_X\Semester_Y\BEE_XXXX_Course\NN_Topic.json
and rebuilds:
    output_slides\BEE\Year_X\Semester_Y\BEE_XXXX_Course\NN_Topic.pptx

Use when:
  - You changed the slide design (colors, logo, footer)
  - A .pptx got corrupted and needs rebuilding
  - You want to refresh all decks quickly

Usage:
    python regenerate_from_cache.py                    # rebuild all
    python regenerate_from_cache.py --missing-only     # only missing pptx
    python regenerate_from_cache.py --course "BEE 1101"
"""

import sys
import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

# Import slide builders from gen_topic.py
from gen_topic import (
    build_title_slide,
    build_content_slide,
    BASE_DIR,
    CACHE_ROOT,
    SLIDES_ROOT,
)


def parse_args():
    args = sys.argv[1:]
    opts = {"missing_only": False, "course": None}
    if "--missing-only" in args:
        opts["missing_only"] = True
    if "--course" in args:
        idx = args.index("--course")
        if idx + 1 < len(args):
            course = args[idx + 1]
            if idx + 2 < len(args) and not args[idx + 2].startswith("--"):
                course = f"{course} {args[idx + 2]}"
            opts["course"] = course.replace("_", " ").strip().upper()
    return opts


def parse_cache_path(cache_file):
    """
    generated_content\\BEE\\Year_1\\Semester_1\\BEE_1101_Communication_Skills\\01_Overview_of_Communication.json
      →
    returns dict with program_code, year, semester, course_folder, topic_stem
    """
    rel = cache_file.relative_to(CACHE_ROOT)
    parts = rel.parts  # ('BEE','Year_1','Semester_1','BEE_1101_Communication_Skills','01_Overview.json')

    if len(parts) < 5:
        return None

    program_code = parts[0]
    try:
        year = int(parts[1].replace("Year_", ""))
        semester = int(parts[2].replace("Semester_", ""))
    except ValueError:
        return None

    course_folder = parts[3]
    topic_stem = Path(parts[4]).stem  # '01_Overview_of_Communication'

    # Recover course_code and course_name from course_folder
    # Format: "BEE_1101_Communication_Skills"
    cf_parts = course_folder.split("_", 2)
    if len(cf_parts) < 3:
        return None
    course_code = f"{cf_parts[0]} {cf_parts[1]}"
    course_name = cf_parts[2].replace("_", " ")

    # Recover topic number and topic name from stem
    # Format: "01_Overview_of_Communication"
    if "_" not in topic_stem:
        return None
    num_str, topic_name = topic_stem.split("_", 1)
    try:
        topic_number = int(num_str)
    except ValueError:
        return None
    topic = topic_name.replace("_", " ")

    return {
        "program_code": program_code,
        "year": year,
        "semester": semester,
        "course_code": course_code,
        "course_name": course_name,
        "topic_number": topic_number,
        "topic": topic,
        "topic_stem": topic_stem,
        "course_folder": course_folder,
    }


def rebuild_one(cache_file):
    info = parse_cache_path(cache_file)
    if info is None:
        return False, "cannot parse cache path"

    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    slides_data = data.get("slides", [])
    if not slides_data:
        return False, "no slides in cache"

    # Output path mirrors cache path
    out_dir = (SLIDES_ROOT / info["program_code"]
               / f"Year_{info['year']}" / f"Semester_{info['semester']}"
               / info["course_folder"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{info['topic_stem']}.pptx"

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    build_title_slide(
        prs,
        info["course_name"], info["course_code"],
        info["topic"], info["topic_number"], 1,
        info["year"], info["semester"]
    )

    total = len(slides_data)
    for i, slide_data in enumerate(slides_data, 1):
        build_content_slide(prs, slide_data, info["course_code"],
                            info["topic"], i, total)

    prs.save(str(out_path))
    return True, str(out_path.relative_to(BASE_DIR))


def main():
    opts = parse_args()

    if not CACHE_ROOT.exists():
        print(f"[INFO] Cache folder missing: {CACHE_ROOT}")
        return

    cache_files = sorted(CACHE_ROOT.rglob("*.json"))

    if opts["course"]:
        needle_a = opts["course"]
        needle_b = opts["course"].replace(" ", "_")
        cache_files = [c for c in cache_files
                       if needle_a in str(c.parent) or needle_b in str(c.parent)]

    if not cache_files:
        print("[INFO] No cached JSON found (or none match filter).")
        return

    print("=" * 78)
    print(f"  Rebuilding {len(cache_files)} decks from cache (no AI calls)")
    if opts["course"]:
        print(f"  Filter: {opts['course']}")
    if opts["missing_only"]:
        print("  Mode:   missing-only")
    print("=" * 78)

    done = skipped = failed = 0

    for cache_file in cache_files:
        info = parse_cache_path(cache_file)
        if info is None:
            print(f"  ❌ {cache_file.relative_to(CACHE_ROOT)} — bad path")
            failed += 1
            continue

        pptx_path = (SLIDES_ROOT / info["program_code"]
                     / f"Year_{info['year']}" / f"Semester_{info['semester']}"
                     / info["course_folder"]
                     / f"{info['topic_stem']}.pptx")

        if opts["missing_only"] and pptx_path.exists():
            skipped += 1
            continue

        try:
            ok, msg = rebuild_one(cache_file)
            if ok:
                print(f"  ✅ {msg}")
                done += 1
            else:
                print(f"  ❌ {cache_file.name} — {msg}")
                failed += 1
        except Exception as e:
            print(f"  ❌ {cache_file.name} — {e}")
            failed += 1

    print("\n" + "=" * 78)
    print(f"  Rebuilt:  {done}")
    print(f"  Skipped:  {skipped}")
    print(f"  Failed:   {failed}")
    print(f"  Output:   {SLIDES_ROOT}")
    print("=" * 78)


if __name__ == "__main__":
    main()
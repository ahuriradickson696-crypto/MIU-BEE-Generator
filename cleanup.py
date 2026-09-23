"""
cleanup.py
Cleans up junk from the MIU nested tree:
  - Empty/tiny .pptx files (failed generations)
  - Corrupt or tiny cached JSON
  - Orphan cache entries (topics no longer in curriculum.json)
  - Orphan PDFs (source pptx missing)
  - Empty leftover folders (Year_X, Semester_Y, Course)

Safe by default — dry run shows what WOULD be deleted.

Usage:
    python cleanup.py                 # dry run
    python cleanup.py --apply         # actually delete
    python cleanup.py --apply --pptx-only   # skip cache/PDF checks
"""

import sys
import json
import shutil
from pathlib import Path

BASE = Path(__file__).parent
CURRICULUM = BASE / "curriculum.json"
CACHE_ROOT = BASE / "generated_content"
SLIDES_ROOT = BASE / "output_slides"
PDFS_ROOT = BASE / "output_pdfs"

MIN_PPTX_SIZE = 20_000
MIN_CACHE_SIZE = 200


def clean_name(text):
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")


def course_dir(course_code, course_name):
    return f"{clean_name(course_code)}_{clean_name(course_name)}"


def topic_stem(num, topic_name):
    return f"{num:02d}_{clean_name(topic_name)}"


def load_expected_paths():
    """Return set of all expected cache paths from curriculum.json."""
    if not CURRICULUM.exists():
        return set()

    with open(CURRICULUM, "r", encoding="utf-8") as f:
        data = json.load(f)

    expected = set()
    for program in data["programs"]:
        pc = program["code"]
        for yb in program["years"]:
            y = yb["year"]
            for sb in yb["semesters"]:
                s = sb["semester"]
                for course in sb["courses"]:
                    cdir = course_dir(course["code"], course["name"])
                    for idx, topic in enumerate(course.get("topics", []), 1):
                        stem = topic_stem(idx, topic)
                        expected.add(
                            CACHE_ROOT / pc / f"Year_{y}" / f"Semester_{s}"
                            / cdir / f"{stem}.json"
                        )
    return expected


def parse_args():
    args = sys.argv[1:]
    return {
        "apply": "--apply" in args,
        "pptx_only": "--pptx-only" in args,
    }


def remove_empty_dirs(root):
    """Remove empty subfolders bottom-up. Keep the root itself."""
    if not root.exists():
        return 0
    removed = 0
    for folder in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
        if folder.is_dir() and not any(folder.iterdir()):
            try:
                folder.rmdir()
                removed += 1
                print(f"  🗑️  empty dir: {folder.relative_to(BASE)}")
            except OSError:
                pass
    return removed


def main():
    opts = parse_args()

    print("=" * 78)
    print("  MIU BEE Cleanup Utility (nested tree)")
    print("=" * 78)
    print(f"  Mode: {'APPLY (deleting)' if opts['apply'] else 'DRY RUN (nothing deleted)'}")
    print("=" * 78)

    to_delete = []

    # ---------- 1. Tiny pptx ----------
    print("\n[1] Tiny/broken .pptx files in output_slides\\ ...")
    if SLIDES_ROOT.exists():
        bad = 0
        for pptx in SLIDES_ROOT.rglob("*.pptx"):
            size = pptx.stat().st_size
            if size < MIN_PPTX_SIZE:
                to_delete.append(("tiny pptx", pptx, f"{size} bytes"))
                print(f"  ⚠️  {pptx.relative_to(BASE)}  ({size} bytes)")
                bad += 1
        if bad == 0:
            print("  ✅ None found")
    else:
        print("  (folder missing)")

    # ---------- 2. Corrupt/tiny cache ----------
    print("\n[2] Corrupt or empty cache files in generated_content\\ ...")
    if CACHE_ROOT.exists():
        bad = 0
        for cache in CACHE_ROOT.rglob("*.json"):
            try:
                if cache.stat().st_size < MIN_CACHE_SIZE:
                    to_delete.append(("tiny cache", cache,
                                      f"{cache.stat().st_size} bytes"))
                    print(f"  ⚠️  {cache.relative_to(BASE)}  (tiny)")
                    bad += 1
                    continue
                with open(cache, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict) or "slides" not in data:
                    to_delete.append(("bad structure", cache, "no 'slides' key"))
                    print(f"  ⚠️  {cache.relative_to(BASE)}  (no slides key)")
                    bad += 1
            except Exception:
                to_delete.append(("corrupt", cache, "unparseable"))
                print(f"  ⚠️  {cache.relative_to(BASE)}  (unparseable)")
                bad += 1
        if bad == 0:
            print("  ✅ None found")
    else:
        print("  (folder missing)")

    # ---------- 3. Orphan cache (not in curriculum) ----------
    if not opts["pptx_only"]:
        print("\n[3] Orphan cache files (not in curriculum.json) ...")
        expected = load_expected_paths()
        if expected and CACHE_ROOT.exists():
            bad = 0
            for cache in CACHE_ROOT.rglob("*.json"):
                if cache.resolve() not in {p.resolve() for p in expected}:
                    to_delete.append(("orphan cache", cache, "not in curriculum"))
                    print(f"  ⚠️  {cache.relative_to(BASE)}")
                    bad += 1
            if bad == 0:
                print("  ✅ None found")
        else:
            print("  (skipped)")

    # ---------- 4. Orphan PDFs ----------
    print("\n[4] Orphan PDFs (source pptx missing) ...")
    if PDFS_ROOT.exists() and SLIDES_ROOT.exists():
        bad = 0
        for pdf in PDFS_ROOT.rglob("*.pdf"):
            rel = pdf.relative_to(PDFS_ROOT)
            expected_pptx = SLIDES_ROOT / rel.with_suffix(".pptx")
            if not expected_pptx.exists():
                to_delete.append(("orphan pdf", pdf, "no matching pptx"))
                print(f"  ⚠️  {pdf.relative_to(BASE)}")
                bad += 1
        if bad == 0:
            print("  ✅ None found")
    else:
        print("  (skipped)")

    # ---------- Summary ----------
    print("\n" + "=" * 78)
    print(f"  Items to delete: {len(to_delete)}")
    if to_delete:
        total_size = sum(p.stat().st_size for _, p, _ in to_delete if p.exists())
        print(f"  Total size:      {total_size / 1024:.1f} KB")

    if not opts["apply"]:
        print("\n  ⚠️  DRY RUN — nothing was deleted.")
        print("  👉 To apply:  python cleanup.py --apply")
        print("=" * 78)
        return

    # ---------- Apply ----------
    print("\n  Deleting...")
    deleted = 0
    for _, path, _ in to_delete:
        try:
            path.unlink()
            deleted += 1
        except Exception as e:
            print(f"  ❌ {path.name}: {e}")
    print(f"\n  ✅ Deleted {deleted} files.")

    # ---------- Empty folders ----------
    print("\n[5] Removing empty subfolders ...")
    empty_n = 0
    for root in (SLIDES_ROOT, CACHE_ROOT, PDFS_ROOT):
        empty_n += remove_empty_dirs(root)
    if empty_n == 0:
        print("  ✅ No empty folders")

    print("=" * 78)


if __name__ == "__main__":
    main()
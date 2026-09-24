"""
Walks the nested MIU cache tree and reports per-course progress.
"""


import json
from pathlib import Path

BASE = Path(__file__).parent
CURRICULUM = BASE / "curriculum.json"
CACHE_ROOT = BASE / "generated_content"
SLIDES_ROOT = BASE / "output_slides"
PDFS_ROOT = BASE / "output_pdfs"


def clean_name(text):
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")


def course_dir(course_code, course_name):
    return f"{clean_name(course_code)}_{clean_name(course_name)}"


def topic_stem(topic_number, topic_name):
    return f"{topic_number:02d}_{clean_name(topic_name)}"


def count_files(folder, extensions):
    if not folder.exists():
        return 0
    n = 0
    for ext in extensions:
        n += len(list(folder.rglob(f"*{ext}")))
    return n


def main():
    with open(CURRICULUM, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 78)
    print("  MIU BEE Slide Generator — Progress Report (nested tree)")
    print("=" * 78)

    grand_total = 0
    grand_done = 0
    grand_courses = 0

    for program in data["programs"]:
        program_code = program["code"]
        print(f"\nProgramme: {program['name']} ({program_code})")

        for year_block in program["years"]:
            year = year_block["year"]

            for semester_block in year_block["semesters"]:
                semester = semester_block["semester"]
                print(f"\n  ── Year {year} · Semester {semester} ──")

                sem_total = 0
                sem_done = 0

                for course in semester_block["courses"]:
                    grand_courses += 1
                    course_code = course["code"]
                    course_name = course["name"]
                    topics = course.get("topics", [])
                    total = len(topics)

                    folder = (CACHE_ROOT / program_code
                              / f"Year_{year}" / f"Semester_{semester}"
                              / course_dir(course_code, course_name))

                    done = 0
                    for idx, topic in enumerate(topics, 1):
                        stem = topic_stem(idx, topic)
                        if (folder / f"{stem}.json").exists():
                            done += 1

                    sem_total += total
                    sem_done += done
                    grand_total += total
                    grand_done += done

                    mark = "✅" if done == total else "⏳" if done > 0 else "❌"
                    pct = (done / total * 100) if total else 0
                    bar = _bar(pct)
                    print(f"    {mark} {course_code:10} {course_name[:38]:40} "
                          f"{done:3}/{total:3}  {bar}")

                pct_sem = (sem_done / sem_total * 100) if sem_total else 0
                print(f"       Semester subtotal: {sem_done}/{sem_total} "
                      f"({pct_sem:.1f}%)")

    pptx_count = count_files(SLIDES_ROOT, [".pptx"])
    pdf_count = count_files(PDFS_ROOT, [".pdf"])

    pct = (grand_done / grand_total * 100) if grand_total else 0
    remaining = grand_total - grand_done

    print("\n" + "=" * 78)
    print("  SUMMARY")
    print("=" * 78)
    print(f"  Courses:        {grand_courses}")
    print(f"  Topics total:   {grand_total}")
    print(f"  Topics done:    {grand_done}")
    print(f"  Topics left:    {remaining}")
    print(f"  Progress:       {pct:.1f}%   {_bar(pct, 30)}")
    print(f"  PPTX files:     {pptx_count}")
    print(f"  PDF files:      {pdf_count}")
    print("=" * 78)

    if remaining > 0:
        print("\n  👉 Run run.bat (or run_all.bat) to continue.\n")
    else:
        print("\n  🎉 All topics complete!\n")


def _bar(pct, width=20):
    filled = int(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


if __name__ == "__main__":
    main()
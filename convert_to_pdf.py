"""
Converts .pptx files to PDF while preserving the MIU nested tree.
"""


import sys
import subprocess
import shutil
from pathlib import Path

BASE = Path(__file__).parent
SLIDES_ROOT = BASE / "output_slides"
PDFS_ROOT = BASE / "output_pdfs"

PDFS_ROOT.mkdir(exist_ok=True)


def parse_args():
    args = sys.argv[1:]
    opts = {"skip_existing": False, "course": None}
    if "--skip-existing" in args:
        opts["skip_existing"] = True
    if "--course" in args:
        idx = args.index("--course")
        if idx + 1 < len(args):
            course = args[idx + 1]
            if idx + 2 < len(args) and not args[idx + 2].startswith("--"):
                course = f"{course} {args[idx + 2]}"
            opts["course"] = course.replace("_", " ").strip().upper()
    return opts


def find_libreoffice():
    candidates = [
        r"C:\\Program Files\LibreOffice\program\soffice.exe",
        r"C:\\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return shutil.which("soffice")


def convert_with_libreoffice(soffice, pptx_path, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        soffice,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(out_dir),
        str(pptx_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return result.returncode == 0


def convert_with_powerpoint(pptx_path, out_dir):
    try:
        import win32com.client  # type: ignore
    except ImportError:
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        powerpoint.Visible = 1
        deck = powerpoint.Presentations.Open(str(pptx_path), WithWindow=False)
        pdf_path = out_dir / (pptx_path.stem + ".pdf")
        deck.SaveAs(str(pdf_path), 32)  # 32 = PDF
        deck.Close()
        return pdf_path.exists()
    except Exception as e:
        print(f"    [powerpoint error] {e}")
        return False


def mirror_path(pptx_path):
    """output_slides\A\B\c.pptx  →  output_pdfs\A\B\c.pdf"""
    rel = pptx_path.relative_to(SLIDES_ROOT)
    return PDFS_ROOT / rel.with_suffix(".pdf")


def main():
    opts = parse_args()

    if not SLIDES_ROOT.exists():
        print(f"[ERROR] {SLIDES_ROOT} not found. Run gen_topic.py first.")
        return

    pptx_files = sorted(SLIDES_ROOT.rglob("*.pptx"))

    # Optional course filter — checks if "BEE 1101" or "BEE_1101" is in path
    if opts["course"]:
        needle_a = opts["course"]
        needle_b = opts["course"].replace(" ", "_")
        pptx_files = [p for p in pptx_files
                      if needle_a in str(p.parent) or needle_b in str(p.parent)]
        if not pptx_files:
            print(f"[INFO] No pptx files match course '{opts['course']}'")
            return

    if not pptx_files:
        print("[INFO] No .pptx files to convert.")
        return

    print("=" * 78)
    print(f"  Converting {len(pptx_files)} PPTX files to PDF")
    if opts["skip_existing"]:
        print("  Mode: skip-existing")
    if opts["course"]:
        print(f"  Filter: {opts['course']}")
    print("=" * 78)

    soffice = find_libreoffice()
    use_powerpoint = False
    if soffice:
        print(f"[INFO] Using LibreOffice: {soffice}\n")
    else:
        print("[INFO] LibreOffice not found — trying PowerPoint COM...\n")
        use_powerpoint = True

    done = skipped = failed = 0

    for pptx in pptx_files:
        pdf_path = mirror_path(pptx)

        if opts["skip_existing"] and pdf_path.exists():
            skipped += 1
            continue

        rel = pptx.relative_to(SLIDES_ROOT)
        print(f"  → {rel}")

        success = False
        if soffice:
            success = convert_with_libreoffice(soffice, pptx, pdf_path.parent)
        elif use_powerpoint:
            success = convert_with_powerpoint(pptx, pdf_path.parent)

        if success and pdf_path.exists():
            done += 1
        else:
            print(f"    [FAILED] {rel}")
            failed += 1

    print("\n" + "=" * 78)
    print(f"  Done:     {done}")
    print(f"  Skipped:  {skipped}")
    print(f"  Failed:   {failed}")
    print(f"  Output:   {PDFS_ROOT}")
    print("=" * 78)


if __name__ == "__main__":
    main()
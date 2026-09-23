# MIU BEE Slide Generator

Automated PowerPoint slide generator for the **Bachelor of Science in Electrical Engineering (BEE)** curriculum at **Metropolitan International University (MIU)**.

Reads the curriculum → uses AI to write teaching content → builds branded `.pptx` decks → converts to PDF.

---

## 🎯 What It Produces

| Output | Where | Format |
|---|---|---|
| Slide decks | `output_slides\` | `.pptx` |
| PDF versions | `output_pdfs\` | `.pdf` |
| Cached AI content | `generated_content\` | `.json` |
| Progress log | `progress.log` | text |

Each deck contains **16 slides**:
1. Title slide (green, MIU logo, course info)
2–16. Content slides (green header, bullets, footer, page number)

---

## ⚡ Quick Start

### First-time setup (once)

```powershell
cd "C:\Users\MAS GLOBAL TECH\Desktop\MIU-BEE-Generator"

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
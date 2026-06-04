# Carnatic Bingo sheet — instructions

## What this project does

1. Keep your **25 bingo prompts** in **`CarnaticBingoSheetBasicOutline.docx`** as separate paragraphs: **`A1.`** through **`E5.`** (exactly 25 lines; same wording is fine every time).
2. Run **`generate_bingo_sheet.py`** — it builds **`output/Bingo sheet-{n}.docx`**.
3. Open the Word file. **Print double-sided** if you want page 2 on the back of page 1.

Each run **shuffles** which prompt appears next to **A1, A2, … E5** so every printed sheet can differ. The **play grid** stays labeled **A–E** and **1–5**; inner cells are **empty** for checks or X’s (all **25** squares count — no free space).

---

## Page 1 (front)

| Order | Content |
|------|--------|
| 1 | Centered title: **The Joy of Music** |
| 2 | Centered subtitle: **Carnatic Bingo — Bingo sheet-{n}** |
| 3 | **Contact block** — six **bold** lines (not a table): Student Name, Parent Name, Parent Email Address, Parent Whatsapp, Teacher, Location — room to write under each |
| 4 | **How to play** — short *italic* paragraph (match a hint → mark that square; mapping reshuffles each print) |
| 5 | **Bingo grid** — header row **1–5**, column **A–E**; interior cells **blank** |
| 6 | **Clues for each square** — bold heading, then **25 lines**: `A1. …` through `E5. …` with this sheet’s clue text |

**Not included:** “Hello,” “What to listen for,” concert pairing lists, or sidebar images.

---

## Page 2 (back)

One **page break** after page 1 — **no blank pages** in between.

1. **Notes table** — **no title line above it**. Header row: **Bingo Cell**, **Song**, **Ragam**, **Thalam**, **Composer**, **Improv (A/T/N/K)**, **Composition Type**, **Concert**. **10** empty data rows, tall rows for handwriting (~10 pt body text in cells).
2. Small gap, then bold **Concert details**.
3. **Concert details table** — **Concert #**, **Date**, **Artist**, **Accompanists**, **Notes (something you noticed)**, **Venue**, **Location**. **10** empty data rows; **Concert #** column header only — cells **left blank** for the user.

Column widths are **even within each table** (portrait US Letter, ~7.4" usable width).

---

## Output file naming

- Pattern: **`Bingo sheet-1.docx`**, **`Bingo sheet-2.docx`**, … (hyphen + number; **no `#`** in the filename).
- Before writing, the script **deletes every** existing **`Bingo sheet-*.docx`** in **`output/`**, then saves **one** new file.
- The number **n** is **one greater than** the highest **`Bingo sheet-*.docx`** number that existed **before** that deletion (so the counter still steps up across runs).

---

## How to run

From the **Bingo** folder:

```bash
python3 generate_bingo_sheet.py
```

| Flag | Meaning |
|------|--------|
| `--source` | Path to the outline `.docx` (default: `CarnaticBingoSheetBasicOutline.docx` in this folder) |
| `--outdir` | Output directory (default: `output/`) |
| `--number` | Force a specific sheet number (optional; normally automatic) |

Requires **Python 3** and **`python-docx`** (see **`requirements.txt`**).

---

## Files in this folder

| File | Purpose |
|------|---------|
| **`CarnaticBingoSheetBasicOutline.docx`** | Master list of 25 **`A1.`…`E5.`** prompts; edit here to change clues |
| **`generate_bingo_sheet.py`** | Builds the Word sheet |
| **`requirements.txt`** | `python-docx` dependency |
| **`output/`** | Generated **`Bingo sheet-{n}.docx`** (only the latest file remains after each run) |
| **`concerts.txt`** | Optional; **not** read by the current script (keep for your own notes or future use) |

---

## Print / pagination note

The document uses **one explicit page break** before page 2. If **page 1** is very long in Word, Word may still **flow** part of it onto a second sheet before the break — use **Print preview** and, if needed, slightly reduce margins or font size in Word for your printer.

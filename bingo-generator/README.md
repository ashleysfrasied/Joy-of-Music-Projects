# Carnatic Bingo Sheet Generator

Automates printable Carnatic concert bingo sheets for The Joy of Music.

## Invoke in Cursor / Claude

Project skill: **`.cursor/skills/bingo-generator/`** (mirrored in `.claude/skills/bingo-generator/`).

```text
/bingo-generator
```

Or say: “make me a new bingo sheet”.

## Developer Quick start

If you want to run this manually you can use the following commands:

```bash
cd bingo-generator
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python carnatic_bingo_generator.py
```

Layout and static content come from `input_reference_bingo_sheet.docx` (edit in Word for formatting). Clues come from `input_bingo_questions.docx`; MCQs from `input_multiple_choice_Q&A.docx`.

### Reference template (`input_reference_bingo_sheet.docx`)

The generator **copies** this file for every new sheet, then only replaces:

- Sheet number in the title (`Bingo Sheet #N`)
- Clue text in the "I Heard" table (labels stay; text is shuffled)
- MCQ question and four options on page 2

Everything else in the template carries through: fonts, margins, logos, colors, headers, the 6×6 grid layout, and static labels like `★ Answer MCQ ★` in the free space.

**Safe to edit in Word (no code change):** formatting, wording of static text, images, page layout that keeps the same table structure.

**Requires code change:** different table sizes (e.g. not 6×6 grid, not 12×2 "I Heard", not 1×1 MCQ cell), different cell labels, or a different number of clues/MCQs.

Output: `completed-bingo-sheets/Carnatic_Bingo_Sheet_001.docx`, `002.docx`, …

## Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

Tests use temporary state/output paths and do not modify production `bingo_state.json`.

## State

`bingo_state.json` tracks sheet number, clue permutations, MCQ rotation, and every generated file.

## Specs

See `docs/specs/001-carnatic-bingo-generator/`.

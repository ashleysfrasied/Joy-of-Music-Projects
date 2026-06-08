---
name: bingo-generator
description: >-
  Generates a new Carnatic Bingo Word sheet from concert-list and MCQ source
  docx files, with rotated clues and multiple-choice questions. Use when the
  user says bingo-generator, make a new bingo sheet, or generate bingo sheet.
---

# bingo-generator

## Working directory

Resolve the repo root, then use `bingo-generator/`:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/bingo-generator"
```

## Steps

1. `cd` to `bingo-generator/` (see above).
2. If `.venv` is missing: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. Confirm `input_reference_bingo_sheet.docx` exists (layout template; edit in Word for formatting).
4. If generator code changed: `.venv/bin/python -m pytest tests/ -v` (must pass before generating).
5. Run: `.venv/bin/python carnatic_bingo_generator.py`
6. Read `bingo_state.json` → last item in `generated_sheets` and report:
   - Sheet number (e.g. `#3`)
   - Full path under `completed-bingo-sheets/`
   - MCQ number used (1–20) and first line of `mcq_question`

## Rules

- Never edit `input_bingo_questions.docx` or `input_multiple_choice_Q&A.docx` during a run (generator reads them).
- Edit `input_reference_bingo_sheet.docx` for layout/formatting; the generator copies it and only replaces sheet number, shuffled clues, and MCQ text. Formatting and static content flow through automatically; changing table sizes or grid structure requires code changes.
- Never overwrite files in `completed-bingo-sheets/`.

## Manual commands

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/bingo-generator"
.venv/bin/python -m pytest tests/ -v
.venv/bin/python carnatic_bingo_generator.py
```

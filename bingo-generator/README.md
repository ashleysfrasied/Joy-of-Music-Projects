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
sips -s format png BrandLogoTJOMWords-SideBySide-WhiteBG.jpg --out logo.png   # once
.venv/bin/python carnatic_bingo_generator.py
```

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

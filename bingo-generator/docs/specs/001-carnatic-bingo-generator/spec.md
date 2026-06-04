# Feature Specification: Carnatic Bingo Sheet Generator

**Feature Branch**: `001-carnatic-bingo-generator`

**Created**: 2026-06-03

**Status**: Draft

**Input**: User description: "Automate repeatable Carnatic Bingo sheet generation from editable Word source files, with unique clue-to-cell assignments per sheet, rotating multiple-choice questions, incrementing sheet numbers from 1, and archived outputs in completed-bingo-sheets/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a New Bingo Sheet (Priority: P1)

Ashley (or a parent) asks the agent to "make a new bingo sheet." The system reads the latest concert clues and MCQs from Word, assigns clues to grid cells differently than prior sheets, picks the next MCQ, increments the sheet number, and saves a new two-page `.docx` under `completed-bingo-sheets/`.

**Why this priority**: This is the core value — a fresh printable sheet for each concert without manual layout work.

**Independent Test**: Run `python3 carnatic_bingo_generator.py` once; confirm `Carnatic_Bingo_Sheet_001.docx` exists with subtitle `Bingo Sheet #1`, 24 labeled clues in "I Heard", and MCQ #1 from the source list on page 2.

**Acceptance Scenarios**:

1. **Given** no prior `bingo_state.json`, **When** the generator runs, **Then** output is `Carnatic_Bingo_Sheet_001.docx` with `Bingo Sheet #1` on pages 1 and 2.
2. **Given** a prior sheet exists in state, **When** the generator runs again, **Then** sheet number increments, filename uses the next zero-padded number, and `past_clue_orders` gains a new permutation not equal to any prior entry.
3. **Given** the concert list Word doc was edited, **When** the generator runs, **Then** the new sheet reflects the updated clue text without code changes.

---

### User Story 2 - Invoke via bingo-generator Skill (Priority: P1)

A user types `bingo-generator` or "make me a new bingo sheet" in Cursor or Claude. The agent runs the generator and reports sheet number, output path, and which MCQ was used.

**Why this priority**: Makes the workflow repeatable for non-developers.

**Independent Test**: Follow `.cursor/skills/bingo-generator/SKILL.md`; agent output includes path under `completed-bingo-sheets/` and MCQ index (1-based).

**Acceptance Scenarios**:

1. **Given** the skill is installed, **When** the user invokes bingo-generator, **Then** the agent runs `python3 carnatic_bingo_generator.py` from the bingo folder and does not modify source docx files.

---

### User Story 3 - Test-Safe Development (Priority: P2)

Developers and agents run pytest before declaring work complete. Tests use temporary state and output directories.

**Why this priority**: Prevents regressions in parsing, rotation, and document structure.

**Independent Test**: `python3 -m pytest tests/ -v` passes without creating files in production `completed-bingo-sheets/`.

**Acceptance Scenarios**:

1. **Given** the test suite, **When** pytest runs, **Then** all tests pass and no test writes to the repo's production `bingo_state.json`.

---

### Edge Cases

- **Fewer than 24 clues in concert list**: Generator fails with a clear error; no partial sheet is written.
- **Fewer than 20 MCQs in MCQ list**: Generator fails with a clear error.
- **Shuffle collision**: If random shuffle matches a prior `past_clue_orders` entry, retry up to 100 times then fail loud.
- **Missing logo file**: Generator fails with a clear error naming `BrandLogoTJOMWords-SideBySide-WhiteBG.jpg`.
- **Manual sample sheet #2**: `Carnatic_Bingo_Sheet_2 finsihed.docx` is reference only; automated numbering still starts at #1 on first run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse exactly 24 concert clues from `Concert list for bingo sheet.docx`, skipping the title paragraph `Bingo quiz concerts`.
- **FR-002**: System MUST parse exactly 20 multiple-choice questions from `Multiple choice question and answer list.docx`, each with four options and an answer letter A–D.
- **FR-003**: System MUST assign clues to cells `A1`–`E5` excluding `C3` (FREE) via a permutation stored in `past_clue_orders` that differs from all prior permutations.
- **FR-004**: System MUST render the "I Heard" table with labels `A1.`–`E5.` (excluding `C3`) and matching clue text in two columns of 12 rows.
- **FR-005**: System MUST leave bingo grid data cells empty (except `C3` showing `★ Answer MCQ ★`).
- **FR-006**: System MUST rotate MCQs using `next_mcq_index` (0-based), advancing modulo 20 after each successful generation.
- **FR-007**: System MUST display `Carnatic Bingo  |  Bingo Sheet #{N}` on page 1 and page 2 where `N` is the current `sheet_number`.
- **FR-008**: System MUST write each new sheet to `completed-bingo-sheets/Carnatic_Bingo_Sheet_{NNN}.docx` without overwriting existing files.
- **FR-009**: System MUST append each generation to `bingo_state.json` → `generated_sheets` with filename, path, timestamp, `mcq_index`, and question text.
- **FR-010**: System MUST include logo `BrandLogoTJOMWords-SideBySide-WhiteBG.jpg` on both pages.
- **FR-011**: System MUST NOT modify source docx files or the finished reference sheet.
- **FR-012**: The `bingo-generator` skill MUST document the exact commands and summary format for agent runs.

### Success Criteria *(mandatory)*

- **SC-001**: `python3 -m pytest tests/ -v` exits 0 before any feature is declared complete.
- **SC-002**: Two consecutive production runs produce distinct `past_clue_orders` entries and `001` / `002` output files.
- **SC-003**: First production run uses MCQ index 0 (displayed as MCQ #1); second run uses index 1.
- **SC-004**: Invoking the bingo-generator skill produces a user-visible summary with output path and sheet number.

## Assumptions

- Python 3 and `python-docx` are available locally.
- Source Word files remain in the bingo project root with the current filenames.
- Grid layout matches `Carnatic_Bingo_Sheet_2 finsihed.docx` (2 pages, 6×6 grid, page-2 tracking tables unchanged except MCQ content).

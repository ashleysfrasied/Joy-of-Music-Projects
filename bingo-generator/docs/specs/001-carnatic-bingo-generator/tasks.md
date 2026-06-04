# Tasks: Carnatic Bingo Sheet Generator

**Input**: Design documents from `docs/specs/001-carnatic-bingo-generator/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: TDD — write and pass all tests in `tests/` before declaring implementation complete.

**Organization**: Phases ordered for dependencies; test tasks precede implementation tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, or US3 from spec.md

## Phase 1: Setup

**Purpose**: Project scaffolding and dependencies.

- [X] T001 Create `requirements.txt` with `python-docx>=1.1.0` and `pytest>=8.0.0`
- [X] T002 Create `tests/conftest.py` with fixtures `bingo_root`, `tmp_state_file`, and `tmp_output_dir` that isolate state from repo `bingo_state.json` and `completed-bingo-sheets/`
- [X] T003 Create empty `completed-bingo-sheets/.gitkeep` and document output directory in `README.md`

---

## Phase 2: Tests First (TDD — blocking)

**Purpose**: Define correctness before implementation. All tests must fail initially, then pass after Phase 3.

**CRITICAL**: Do not mark feature complete until every test below passes.

### Parser tests

- [X] T004 [P] [US1] Add `tests/test_parse_concert_list.py` asserting `parse_concert_clues` returns 24 strings from `Concert list for bingo sheet.docx` and excludes title `Bingo quiz concerts` (covers FR-001)
- [X] T005 [P] [US1] Add `tests/test_parse_mcqs.py` asserting `parse_mcqs` returns 20 items with `question`, `options` (len 4), and `answer` in `A`–`D` from `Multiple choice question and answer list.docx` (covers FR-002)

### State and rotation tests

- [X] T006 [P] [US1] Add `tests/test_state.py` asserting first `next_generation_params` yields `sheet_number` 1 and appends to `generated_sheets` with path under `tmp_output_dir` (covers FR-007, FR-008, FR-009)
- [X] T007 [P] [US1] Add `tests/test_shuffle.py` asserting two consecutive orders differ and both are stored in `past_clue_orders` (covers FR-003)
- [X] T008 [P] [US1] Add `tests/test_mcq_rotation.py` asserting first run uses `mcq_index` 0 and second run uses 1 with isolated state (covers FR-006)

### Document integration test

- [X] T009 [US1] Add `tests/test_generate_docx.py` calling `generate_sheet` with tmp dirs; assert output file exists, subtitle contains `Bingo Sheet #1`, bingo grid cell `A1` is empty, cell `C3` contains `★ Answer MCQ ★`, page-2 MCQ cell contains first parsed question text, and "I Heard" table has 24 labeled rows excluding `C3` (covers FR-004, FR-005, FR-007, FR-010)

**Checkpoint**: `python3 -m pytest tests/ -v` — tests exist; expected failure until Phase 3 (SC-001 setup).

---

## Phase 3: Implementation (User Story 1 — MVP)

**Purpose**: Make all Phase 2 tests pass.

- [X] T010 [US1] Create `carnatic_bingo_generator.py` with `parse_concert_clues` and `parse_mcqs` implementing FR-001 and FR-002
- [X] T011 [US1] Add `load_state`, `save_state`, and `next_generation_params` functions in `carnatic_bingo_generator.py` implementing FR-003, FR-006, FR-007, FR-008, FR-009
- [X] T012 [US1] Port `build_bingo_docx` from `carnatic_bingo_generator (2).py.txt` using JPG logo path `BrandLogoTJOMWords-SideBySide-WhiteBG.jpg` and dynamic clue map (FR-004, FR-005, FR-010)
- [X] T013 [US1] Add `generate_sheet` and `main()` in `carnatic_bingo_generator.py` writing only to `completed-bingo-sheets/` and never opening source docx for write (FR-011)
- [X] T014 [US1] Run `python3 -m pytest tests/ -v` and fix failures until exit code 0 (SC-001)

**Checkpoint**: US1 complete — one command produces valid `Carnatic_Bingo_Sheet_001.docx`.

---

## Phase 4: bingo-generator Skill (User Story 2)

**Purpose**: Repeatable agent workflow.

- [X] T015 [US2] Add `.cursor/skills/bingo-generator/SKILL.md` with frontmatter `name: bingo-generator`, trigger description, and steps: install deps, run pytest if code changed, run `python3 carnatic_bingo_generator.py`, summarize from `bingo_state.json` (FR-012, SC-004)
- [X] T016 [P] [US2] Add `.claude/skills/bingo-generator/SKILL.md` mirroring `.cursor/skills/bingo-generator/SKILL.md`
- [X] T017 [US2] Add `README.md` sections: invoke skill, manual CLI, test command, source file list

**Checkpoint**: Agent can invoke skill without reading implementation source.

---

## Phase 5: Validation

**Purpose**: Production smoke test after unit tests green.

- [X] T018 [US1] Run `python3 carnatic_bingo_generator.py` twice in bingo root; verify `completed-bingo-sheets/Carnatic_Bingo_Sheet_001.docx` and `002.docx` exist (SC-002)
- [X] T019 [US1] Verify `bingo_state.json` `generated_sheets` has two entries with different `past_clue_orders` permutations (SC-002, SC-003)
- [X] T020 [US3] Confirm pytest run does not modify production `bingo_state.json` when tests use conftest tmp paths (SC-001, constitution principle I)

---

## Dependencies

| Task | Depends on |
|------|------------|
| T004–T009 | T001, T002 |
| T010–T014 | T004–T009 |
| T015–T017 | T014 |
| T018–T020 | T014 |

## Parallel Example

```bash
# After T002, launch parser tests together:
# T004, T005, T006, T007, T008 in parallel
```

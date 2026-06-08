"""Pytest fixtures — isolated state/output; never touch production paths in tests."""

import os
from pathlib import Path

import pytest

BINGO_ROOT = Path(__file__).resolve().parent.parent

CONCERT_DOCX = BINGO_ROOT / "input_bingo_questions.docx"
MCQ_DOCX = BINGO_ROOT / "input_multiple_choice_Q&A.docx"


@pytest.fixture
def bingo_root():
    return BINGO_ROOT


@pytest.fixture
def tmp_state_file(tmp_path):
    return str(tmp_path / "bingo_state.json")


@pytest.fixture
def tmp_output_dir(tmp_path):
    out = tmp_path / "completed-bingo-sheets"
    out.mkdir()
    return str(out)


@pytest.fixture
def env_isolated(monkeypatch, tmp_state_file, tmp_output_dir):
    """Point generator at temp state and output for integration tests."""
    monkeypatch.setenv("BINGO_STATE_FILE", tmp_state_file)
    monkeypatch.setenv("BINGO_OUTPUT_DIR", tmp_output_dir)
    monkeypatch.setenv("BINGO_ROOT", str(BINGO_ROOT))


@pytest.fixture
def production_state_mtime(bingo_root):
    """Snapshot production state mtime so T020 can assert tests did not touch it."""
    path = bingo_root / "bingo_state.json"
    if path.exists():
        return path.stat().st_mtime
    return None

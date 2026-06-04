from pathlib import Path

import pytest

from carnatic_bingo_generator import generate_sheet


def test_pytest_does_not_modify_production_state(
    env_isolated, tmp_state_file, tmp_output_dir, bingo_root, production_state_mtime
):
    generate_sheet(state_path=tmp_state_file, output_dir=tmp_output_dir)
    prod = Path(bingo_root) / "bingo_state.json"
    if production_state_mtime is None:
        assert not prod.exists()
    else:
        assert prod.stat().st_mtime == production_state_mtime

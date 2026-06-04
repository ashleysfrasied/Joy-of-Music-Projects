from carnatic_bingo_generator import generate_sheet, load_state


def test_mcq_index_rotates(env_isolated, tmp_state_file, tmp_output_dir):
    entry1 = generate_sheet(state_path=tmp_state_file, output_dir=tmp_output_dir)
    assert entry1["mcq_index"] == 0

    entry2 = generate_sheet(state_path=tmp_state_file, output_dir=tmp_output_dir)
    assert entry2["mcq_index"] == 1

    state = load_state(tmp_state_file)
    assert state["next_mcq_index"] == 2

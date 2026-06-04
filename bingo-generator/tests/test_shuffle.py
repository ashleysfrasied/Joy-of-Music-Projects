from carnatic_bingo_generator import generate_sheet, load_state


def test_two_runs_have_different_clue_orders(env_isolated, tmp_state_file, tmp_output_dir):
    generate_sheet(state_path=tmp_state_file, output_dir=tmp_output_dir)
    generate_sheet(state_path=tmp_state_file, output_dir=tmp_output_dir)
    state = load_state(tmp_state_file)
    assert len(state["past_clue_orders"]) == 2
    assert state["past_clue_orders"][0] != state["past_clue_orders"][1]

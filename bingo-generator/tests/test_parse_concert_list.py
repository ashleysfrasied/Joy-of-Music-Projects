from conftest import CONCERT_DOCX

from carnatic_bingo_generator import CONCERT_TITLE_SKIP, EXPECTED_CLUES, parse_concert_clues


def test_parse_concert_clues_count_and_title(bingo_root):
    clues = parse_concert_clues(str(CONCERT_DOCX))
    assert len(clues) == EXPECTED_CLUES
    assert CONCERT_TITLE_SKIP not in clues
    assert all(c.strip() for c in clues)

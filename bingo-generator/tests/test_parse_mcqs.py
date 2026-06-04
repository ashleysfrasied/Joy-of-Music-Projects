from conftest import MCQ_DOCX

from carnatic_bingo_generator import EXPECTED_MCQS, parse_mcqs


def test_parse_mcqs_structure(bingo_root):
    mcqs = parse_mcqs(str(MCQ_DOCX))
    assert len(mcqs) == EXPECTED_MCQS
    for m in mcqs:
        assert m["question"]
        assert len(m["options"]) == 4
        assert m["answer"] in "ABCD"

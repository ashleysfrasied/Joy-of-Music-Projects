from pathlib import Path

from build_quiz_video import (
    normalize_stem,
    performer_key_from_audio,
    score_image_match,
    strip_display_markdown,
)


def test_normalize_stem_strips_punctuation():
    assert normalize_stem("K. V. N.") == "kvn"
    assert normalize_stem("Lalgudi2013") == "lalgudi2013"


def test_performer_key_from_hyphenated_mp3():
    assert performer_key_from_audio(Path("KVN-Hindolam.mp3")) == "KVN"
    assert performer_key_from_audio(Path("Lalgudi-Hindolam.mp3")) == "Lalgudi"


def test_score_image_match_exact_beats_partial():
    exact = score_image_match("KVN", Path("KVN.jpg"))
    partial = score_image_match("KVN", Path("KVN2.jpeg"))
    assert exact is not None and partial is not None
    assert exact < partial


def test_score_image_match_ignores_non_images():
    assert score_image_match("KVN", Path("notes.txt")) is None


def test_strip_display_markdown():
    assert strip_display_markdown("Find the **odd** one out") == "Find the odd one out"
    assert strip_display_markdown("*emphasis*") == "emphasis"


def test_local_source_naming_matches_fetch_script():
    """GCS basename + album prefix = local filename from fetch_audio_clips.sh."""
    gcs_name = "01-SreeMahaaganapatiravatuMaam.mp3"
    local_prefix = "AKCNatarajan_Album-001"
    assert f"{local_prefix}_{gcs_name}" == (
        "AKCNatarajan_Album-001_01-SreeMahaaganapatiravatuMaam.mp3"
    )

from pathlib import Path

from build_quiz_video import (
    build_quiz_metadata,
    next_completed_quiz_output,
    next_completed_video_path,
    normalize_stem,
    performer_key_from_audio,
    ragam_from_audio,
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


def test_ragam_from_hyphenated_mp3():
    assert ragam_from_audio(Path("KVN-Hindolam.mp3")) == "Hindolam"
    assert ragam_from_audio(Path("MSG-Hamsanandi.mp3")) == "Hamsanandi"


def test_next_completed_quiz_output_starts_at_one(tmp_path):
    quiz_dir, video_path, quiz_num = next_completed_quiz_output(tmp_path)
    assert quiz_num == 1
    assert quiz_dir == tmp_path / "Quiz1"
    assert video_path == tmp_path / "Quiz1" / "Quiz1_video.mp4"


def test_next_completed_quiz_output_increments_from_dirs_and_legacy_files(tmp_path):
    (tmp_path / "Quiz1").mkdir()
    (tmp_path / "Quiz3_video.mp4").write_bytes(b"x")
    quiz_dir, video_path, quiz_num = next_completed_quiz_output(tmp_path)
    assert quiz_num == 4
    assert quiz_dir == tmp_path / "Quiz4"
    assert video_path == tmp_path / "Quiz4" / "Quiz4_video.mp4"


def test_next_completed_video_path_uses_quiz_folder(tmp_path):
    assert next_completed_video_path(tmp_path) == tmp_path / "Quiz1" / "Quiz1_video.mp4"


def test_build_quiz_metadata_marks_odd_clip():
    audios = [
        Path("KVN-Hindolam.mp3"),
        Path("Lalgudi-Hindolam.mp3"),
        Path("VijaySiva-Hindolam.mp3"),
        Path("MSG-Hamsanandi.mp3"),
    ]
    performers = {
        "KVN": "K. V. Narayanaswamy",
        "Lalgudi": "Lalgudi G. Jayaraman",
        "VijaySiva": "Vijay Siva",
        "MSG": "M. S. Gopalakrishnan",
    }
    md = build_quiz_metadata(1, audios, performers)
    assert "# Quiz 1 — Hindolam vs Hamsanandi" in md
    assert "| 4 (odd) | M. S. Gopalakrishnan | Hamsanandi | MSG-Hamsanandi.mp3 |" in md


def test_next_completed_video_path_starts_at_one(tmp_path):
    assert next_completed_video_path(tmp_path) == tmp_path / "Quiz1" / "Quiz1_video.mp4"


def test_next_completed_video_path_increments_from_highest(tmp_path):
    (tmp_path / "Quiz1" / "Quiz1_video.mp4").parent.mkdir(parents=True)
    (tmp_path / "Quiz1" / "Quiz1_video.mp4").write_bytes(b"x")
    (tmp_path / "Quiz3").mkdir()
    assert next_completed_video_path(tmp_path) == tmp_path / "Quiz4" / "Quiz4_video.mp4"


def test_local_source_naming_matches_fetch_script():
    """GCS basename + album prefix = local filename from fetch_audio_clips.sh."""
    gcs_name = "01-SreeMahaaganapatiravatuMaam.mp3"
    local_prefix = "AKCNatarajan_Album-001"
    assert f"{local_prefix}_{gcs_name}" == (
        "AKCNatarajan_Album-001_01-SreeMahaaganapatiravatuMaam.mp3"
    )

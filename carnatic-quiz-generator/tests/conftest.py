"""Shared fixtures for carnatic-quiz-generator tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from music_index import Track, local_audio_name

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def mini_csv() -> Path:
    return FIXTURES / "mini_music_index.csv"


@pytest.fixture
def mini_pairs() -> Path:
    return FIXTURES / "mini_ragam_pairs.json"


@pytest.fixture
def musicians_path() -> Path:
    return ROOT / "musicians.json"


@pytest.fixture
def pics_dir() -> Path:
    return ROOT / "Pics"


@pytest.fixture
def performers_path() -> Path:
    return ROOT / "performers.json"


@pytest.fixture
def production_csv() -> Path:
    return ROOT / "MasterWebAppMusicIndex.csv"


@pytest.fixture
def production_pairs() -> Path:
    return ROOT / "ragam_pairs.json"


def make_track(
    *,
    song: str = "Test Song",
    ragam: str = "Hindolam",
    musician: str = "PalghatKVNarayanaswamy",
    concert_folder: str = "Album-018",
    file_name: str = "01-test.mp3",
    relative_path: str | None = None,
    track_type: str = "Vocal",
) -> Track:
    rel = relative_path or f"{musician}/{concert_folder}/{file_name}"
    return Track(
        song=song,
        ragam=ragam,
        musician=musician,
        concert_folder=concert_folder,
        file_name=file_name,
        relative_path=rel,
        main_artist="Test Artist",
        track_type=track_type,
    )


def seed_mini_audio(audio_dir: Path, csv_path: Path, musician_map: dict[str, str]) -> int:
    """Create stub local MP3s for all mapped vocal tracks in a fixture CSV."""
    import csv

    count = 0
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("Type") != "Vocal":
                continue
            musician = row.get("Musician", "")
            if musician not in musician_map:
                continue
            name = f"{musician}_{row['ConcertFolder']}_{row['FileName']}"
            (audio_dir / name).write_bytes(b"fake-mp3")
            count += 1
    return count


def assert_valid_selection(
    selection,
    musician_map: dict[str, str],
    pairs_path: Path,
    audio_dir: Path,
    pics_dir: Path | None = None,
) -> None:
    """Shared assertions for a QuizSelection result."""
    import json

    from select_quiz_tracks import load_ragam_pairs

    assert selection.main_ragam != selection.odd_ragam
    assert len(selection.main_tracks) == 3
    assert all(t.ragam == selection.main_ragam for t in selection.main_tracks)
    assert selection.odd_track.ragam == selection.odd_ragam

    pairs = load_ragam_pairs(pairs_path)
    assert any(p.main == selection.main_ragam and p.odd == selection.odd_ragam for p in pairs)

    data = selection.to_dict(musician_map, pics_dir=pics_dir)
    assert len(data["clips"]) == 4
    assert data["clips"][0]["slot"] == 1
    assert data["clips"][3]["slot"] == 4
    assert data["clips"][3]["is_odd"] is True
    assert not any(c.get("is_odd") for c in data["clips"][:3])

    for clip in data["clips"]:
        assert clip["performer_key"]
        assert musician_map[clip["musician"]] == clip["performer_key"]
        local_path = audio_dir / clip["local_audio_name"]
        assert local_path.is_file(), f"Missing local file: {local_path}"
        assert clip["gcs_path"].startswith("gs://mwappv1-carnatic/")
        assert clip["ragam"] in (selection.main_ragam, selection.odd_ragam)
        if pics_dir is not None:
            assert clip.get("pic_path"), f"No Pics match for {clip['performer_key']!r}"
            assert Path(clip["pic_path"]).is_file()

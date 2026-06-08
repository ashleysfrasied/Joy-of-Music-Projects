"""Integration test for validate_selection.py against production CSV."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_production_csv_selection_with_seeded_audio(tmp_path):
    # Use isolated audio dir so we don't depend on workspace state
    audio_dir = tmp_path / "audio-clips"
    audio_dir.mkdir()

    # Seed via validate logic in subprocess with modified env - simpler: run core selection
    from music_index import filter_eligible, load_musician_map, load_tracks, local_audio_name
    from select_quiz_tracks import load_ragam_pairs, select_quiz_tracks
    from tests.conftest import assert_valid_selection

    csv_path = ROOT / "MasterWebAppMusicIndex.csv"
    pairs_path = ROOT / "ragam_pairs.json"
    musicians_path = ROOT / "musicians.json"
    pics_dir = ROOT / "Pics"
    musician_map = load_musician_map(musicians_path)
    pairs = load_ragam_pairs(pairs_path)
    wanted = {p.main for p in pairs} | {p.odd for p in pairs}

    per_ragam: dict[str, int] = {}
    eligible = filter_eligible(
        load_tracks(csv_path),
        audio_dir=audio_dir,
        musician_map=musician_map,
        pics_dir=pics_dir,
        require_local=False,
    )
    for track in eligible:
        if track.ragam not in wanted:
            continue
        if per_ragam.get(track.ragam, 0) >= 6:
            continue
        (audio_dir / local_audio_name(track)).write_bytes(b"stub")
        per_ragam[track.ragam] = per_ragam.get(track.ragam, 0) + 1

    selection = select_quiz_tracks(
        csv_path=csv_path,
        pairs_path=pairs_path,
        musicians_path=musicians_path,
        audio_dir=audio_dir,
        pics_dir=pics_dir,
        seed=42,
    )
    assert_valid_selection(selection, musician_map, pairs_path, audio_dir, pics_dir=pics_dir)

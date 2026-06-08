#!/usr/bin/env python3
"""
Seed local stub MP3s from production CSV for a known ragam pair, run selection,
and validate the output. Use when GCS fetch is unavailable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from music_index import filter_eligible, load_musician_map, load_tracks, local_audio_name
from select_quiz_tracks import format_selection, load_ragam_pairs, select_quiz_tracks
from tests.conftest import assert_valid_selection

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "MasterWebAppMusicIndex.csv"
PAIRS = ROOT / "ragam_pairs.json"
MUSICIANS = ROOT / "musicians.json"
AUDIO_DIR = ROOT / "audio-clips"
PICS = ROOT / "Pics"

# Seed enough production tracks for all pairs that have mapped vocal performers.
TARGET_PAIRS = [
    ("Hindolam", "Hamsanandi"),
    ("Kambhoji", "Harikambhoji"),
    ("Kharaharapriya", "Bhairavi"),
]


def seed_production_stubs(audio_dir: Path, max_per_ragam: int = 8) -> int:
    tracks = load_tracks(CSV)
    musician_map = load_musician_map(MUSICIANS)
    pairs = load_ragam_pairs(PAIRS)
    wanted_ragams = {p.main for p in pairs} | {p.odd for p in pairs}
    eligible = filter_eligible(
        tracks,
        audio_dir=audio_dir,
        musician_map=musician_map,
        pics_dir=PICS,
        require_local=False,
    )
    eligible_by_ragam = {r: [] for r in wanted_ragams}
    for track in eligible:
        if track.ragam in eligible_by_ragam:
            eligible_by_ragam[track.ragam].append(track)

    seeded = 0
    per_ragam: dict[str, int] = {}
    for ragam, ragam_tracks in eligible_by_ragam.items():
        for track in ragam_tracks:
            if per_ragam.get(ragam, 0) >= max_per_ragam:
                break
            path = audio_dir / local_audio_name(track)
            if path.is_file():
                continue
            path.write_bytes(b"validation-stub")
            per_ragam[ragam] = per_ragam.get(ragam, 0) + 1
            seeded += 1
    return seeded


def main() -> int:
    AUDIO_DIR.mkdir(exist_ok=True)
    musician_map = load_musician_map(MUSICIANS)

    seeded = seed_production_stubs(AUDIO_DIR)
    print(f"Seeded {seeded} stub MP3(s) into {AUDIO_DIR}")

    eligible = filter_eligible(
        load_tracks(CSV),
        audio_dir=AUDIO_DIR,
        musician_map=musician_map,
        pics_dir=PICS,
    )
    print(f"Eligible local vocal tracks: {len(eligible)}")

    selection = select_quiz_tracks(
        csv_path=CSV,
        pairs_path=PAIRS,
        musicians_path=MUSICIANS,
        audio_dir=AUDIO_DIR,
        pics_dir=PICS,
        seed=42,
    )

    assert_valid_selection(selection, musician_map, PAIRS, AUDIO_DIR, pics_dir=PICS)

    print()
    print(format_selection(selection, musician_map, pics_dir=PICS))
    print()
    print("Validation: PASSED")
    print(json.dumps(selection.to_dict(musician_map, pics_dir=PICS), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

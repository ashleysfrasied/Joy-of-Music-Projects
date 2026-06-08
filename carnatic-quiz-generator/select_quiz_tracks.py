#!/usr/bin/env python3
"""Randomly select 3+1 quiz tracks (same ragam + similar odd ragam) from the music index."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

from music_index import (
    Track,
    filter_eligible,
    group_by_ragam,
    load_musician_map,
    load_tracks,
    performer_key_for_musician,
    performer_photo_path,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / "MasterWebAppMusicIndex.csv"
DEFAULT_PAIRS = ROOT / "ragam_pairs.json"
DEFAULT_MUSICIANS = ROOT / "musicians.json"
DEFAULT_AUDIO_DIR = ROOT / "audio-clips"
DEFAULT_PICS_DIR = ROOT / "Pics"


@dataclass(frozen=True)
class RagamPair:
    main: str
    odd: str


@dataclass
class QuizSelection:
    main_ragam: str
    odd_ragam: str
    main_tracks: list[Track]
    odd_track: Track
    seed: int | None

    def clips(self, musician_map: dict[str, str], pics_dir: Path | None = None) -> list[dict]:
        clips: list[dict] = []
        for i, track in enumerate(self.main_tracks, start=1):
            key = performer_key_for_musician(track.musician, musician_map)
            clip = track.to_dict(performer_key=key, slot=i, is_odd=False)
            if pics_dir is not None and key is not None:
                pic = performer_photo_path(key, pics_dir)
                if pic is not None:
                    clip["pic_path"] = str(pic)
            clips.append(clip)
        key = performer_key_for_musician(self.odd_track.musician, musician_map)
        clip = self.odd_track.to_dict(performer_key=key, slot=4, is_odd=True)
        if pics_dir is not None and key is not None:
            pic = performer_photo_path(key, pics_dir)
            if pic is not None:
                clip["pic_path"] = str(pic)
        clips.append(clip)
        return clips

    def to_dict(self, musician_map: dict[str, str], pics_dir: Path | None = None) -> dict:
        return {
            "main_ragam": self.main_ragam,
            "odd_ragam": self.odd_ragam,
            "clips": self.clips(musician_map, pics_dir=pics_dir),
            "seed": self.seed,
        }


def load_ragam_pairs(path: Path) -> list[RagamPair]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [RagamPair(main=p["main"], odd=p["odd"]) for p in data["pairs"]]


def sample_main_tracks(tracks: list[Track], count: int = 3) -> list[Track]:
    """Pick `count` tracks, preferring distinct musicians when possible."""
    if len(tracks) < count:
        raise ValueError(f"Need at least {count} tracks, got {len(tracks)}")

    by_musician: dict[str, list[Track]] = {}
    for track in tracks:
        by_musician.setdefault(track.musician, []).append(track)

    if len(by_musician) >= count:
        musicians = random.sample(list(by_musician.keys()), count)
        return [random.choice(by_musician[m]) for m in musicians]

    return random.sample(tracks, count)


def valid_pairs(
    pairs: list[RagamPair],
    by_ragam: dict[str, list[Track]],
) -> list[RagamPair]:
    valid: list[RagamPair] = []
    for pair in pairs:
        main_tracks = by_ragam.get(pair.main, [])
        odd_tracks = by_ragam.get(pair.odd, [])
        if len(main_tracks) >= 3 and len(odd_tracks) >= 1:
            valid.append(pair)
    return valid


def select_quiz_tracks(
    *,
    csv_path: Path,
    pairs_path: Path,
    musicians_path: Path,
    audio_dir: Path,
    pics_dir: Path,
    seed: int | None = None,
) -> QuizSelection:
    if seed is not None:
        random.seed(seed)

    tracks = load_tracks(csv_path)
    musician_map = load_musician_map(musicians_path)
    eligible = filter_eligible(
        tracks,
        audio_dir=audio_dir,
        musician_map=musician_map,
        pics_dir=pics_dir,
        require_local=True,
        require_performer_photo=True,
    )
    by_ragam = group_by_ragam(eligible)
    pairs = load_ragam_pairs(pairs_path)
    choices = valid_pairs(pairs, by_ragam)

    if not choices:
        local_count = len(list(audio_dir.glob("*.mp3"))) if audio_dir.is_dir() else 0
        raise SystemExit(
            "No valid ragam pairs with enough local vocal tracks.\n"
            f"  Local MP3s in {audio_dir}: {local_count}\n"
            f"  Eligible vocal tracks (local + mapped performer + photo): {len(eligible)}\n"
            "  Fetch more albums with ./fetch_audio_clips.sh or ./fetch_album.sh <Musician> <ConcertFolder>\n"
            "  See audio-clips/README.md for starter albums."
        )

    pair = random.choice(choices)
    main_tracks = sample_main_tracks(by_ragam[pair.main], 3)
    odd_track = random.choice(by_ragam[pair.odd])

    return QuizSelection(
        main_ragam=pair.main,
        odd_ragam=pair.odd,
        main_tracks=main_tracks,
        odd_track=odd_track,
        seed=seed,
    )


def format_selection(
    selection: QuizSelection,
    musician_map: dict[str, str],
    pics_dir: Path | None = None,
) -> str:
    lines = [
        f"Main ragam: {selection.main_ragam} (3 clips)",
        f"Odd ragam:  {selection.odd_ragam} (clip 4)",
        "",
    ]
    for clip in selection.clips(musician_map, pics_dir=pics_dir):
        label = "ODD" if clip.get("is_odd") else f"clip {clip['slot']}"
        lines.append(
            f"  [{label}] {clip['performer_key']} — {clip['song']} ({clip['ragam']})"
        )
        lines.append(f"           local: {clip['local_audio_name']}")
        lines.append(f"           gcs:   {clip['gcs_path']}")
        if clip.get("pic_path"):
            lines.append(f"           pic:   {Path(clip['pic_path']).name}")
    if selection.seed is not None:
        lines.append(f"\nSeed: {selection.seed}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Select 3+1 quiz tracks from MasterWebAppMusicIndex.csv (random similar ragam pair)."
    )
    p.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Music index CSV path")
    p.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS, help="Similar ragam pairs JSON")
    p.add_argument("--musicians", type=Path, default=DEFAULT_MUSICIANS, help="Musician → performer key map")
    p.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR, help="Local source audio directory")
    p.add_argument("--pics-dir", type=Path, default=DEFAULT_PICS_DIR, help="Performer photos directory")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducible selection")
    p.add_argument("--json", action="store_true", help="Print JSON result to stdout")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    musician_map = load_musician_map(args.musicians)
    selection = select_quiz_tracks(
        csv_path=args.csv,
        pairs_path=args.pairs,
        musicians_path=args.musicians,
        audio_dir=args.audio_dir,
        pics_dir=args.pics_dir,
        seed=args.seed,
    )

    if args.json:
        print(json.dumps(selection.to_dict(musician_map, pics_dir=args.pics_dir), indent=2))
    else:
        print(format_selection(selection, musician_map, pics_dir=args.pics_dir))


if __name__ == "__main__":
    main()

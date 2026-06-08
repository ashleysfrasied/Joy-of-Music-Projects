"""Load and filter tracks from MasterWebAppMusicIndex.csv for quiz selection."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from build_quiz_video import find_performer_image

GCS_BUCKET = "mwappv1-carnatic"
EXCLUDED_RAGAMS = frozenset({"Ragamalika"})


@dataclass(frozen=True)
class Track:
    song: str
    ragam: str
    musician: str
    concert_folder: str
    file_name: str
    relative_path: str
    main_artist: str
    track_type: str

    @property
    def gcs_path(self) -> str:
        return f"gs://{GCS_BUCKET}/{self.relative_path}"

    def to_dict(self, *, performer_key: str | None = None, slot: int | None = None, is_odd: bool = False) -> dict:
        data = {
            "song": self.song,
            "ragam": self.ragam,
            "musician": self.musician,
            "concert_folder": self.concert_folder,
            "file_name": self.file_name,
            "relative_path": self.relative_path,
            "local_audio_name": local_audio_name(self),
            "gcs_path": self.gcs_path,
            "main_artist": self.main_artist,
            "type": self.track_type,
        }
        if performer_key is not None:
            data["performer_key"] = performer_key
        if slot is not None:
            data["slot"] = slot
        if is_odd:
            data["is_odd"] = True
        return data


def load_tracks(csv_path: Path) -> list[Track]:
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = csv.DictReader(f)
        tracks: list[Track] = []
        for row in rows:
            ragam = (row.get("Ragam") or "").strip()
            file_name = (row.get("FileName") or "").strip()
            musician = (row.get("Musician") or "").strip()
            concert_folder = (row.get("ConcertFolder") or "").strip()
            if not file_name or not musician or not concert_folder:
                continue
            tracks.append(
                Track(
                    song=(row.get("Song") or "").strip() or "?",
                    ragam=ragam,
                    musician=musician,
                    concert_folder=concert_folder,
                    file_name=file_name,
                    relative_path=(row.get("RelativePath") or "").strip()
                    or f"{musician}/{concert_folder}/{file_name}",
                    main_artist=(row.get("MainArtist") or "").strip(),
                    track_type=(row.get("Type") or "").strip(),
                )
            )
        return tracks


def local_audio_name(track: Track) -> str:
    return f"{track.musician}_{track.concert_folder}_{track.file_name}"


def local_audio_path(track: Track, audio_dir: Path) -> Path:
    return audio_dir / local_audio_name(track)


def load_musician_map(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    import json

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def performer_key_for_musician(musician: str, musician_map: dict[str, str]) -> str | None:
    return musician_map.get(musician)


def has_performer_photo(performer_key: str, pics_dir: Path) -> bool:
    if not pics_dir.is_dir():
        return False
    try:
        find_performer_image(pics_dir, performer_key)
    except FileNotFoundError:
        return False
    return True


def performer_photo_path(performer_key: str, pics_dir: Path) -> Path | None:
    if not pics_dir.is_dir():
        return None
    try:
        return find_performer_image(pics_dir, performer_key)
    except FileNotFoundError:
        return None


def filter_eligible(
    tracks: list[Track],
    *,
    audio_dir: Path,
    musician_map: dict[str, str],
    pics_dir: Path | None = None,
    vocal_only: bool = True,
    require_local: bool = True,
    require_performer_photo: bool = True,
) -> list[Track]:
    eligible: list[Track] = []
    for track in tracks:
        if vocal_only and track.track_type != "Vocal":
            continue
        if not track.ragam or track.ragam in EXCLUDED_RAGAMS:
            continue
        performer_key = performer_key_for_musician(track.musician, musician_map)
        if performer_key is None:
            continue
        if require_performer_photo and pics_dir is not None:
            if not has_performer_photo(performer_key, pics_dir):
                continue
        if require_local and not local_audio_path(track, audio_dir).is_file():
            continue
        eligible.append(track)
    return eligible


def group_by_ragam(tracks: list[Track]) -> dict[str, list[Track]]:
    grouped: dict[str, list[Track]] = {}
    for track in tracks:
        grouped.setdefault(track.ragam, []).append(track)
    return grouped

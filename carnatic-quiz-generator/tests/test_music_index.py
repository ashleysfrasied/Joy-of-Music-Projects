"""Tests for music_index.py — CSV loading and track filtering."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from music_index import (
    EXCLUDED_RAGAMS,
    GCS_BUCKET,
    Track,
    filter_eligible,
    group_by_ragam,
    load_musician_map,
    load_tracks,
    local_audio_name,
    local_audio_path,
    performer_key_for_musician,
)
from tests.conftest import make_track, seed_mini_audio

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestTrack:
    def test_gcs_path_uses_bucket_and_relative_path(self):
        track = make_track(relative_path="PalghatKVNarayanaswamy/Album-018/01-A.mp3")
        assert track.gcs_path == f"gs://{GCS_BUCKET}/PalghatKVNarayanaswamy/Album-018/01-A.mp3"

    def test_to_dict_includes_all_base_fields(self):
        track = make_track()
        data = track.to_dict(performer_key="KVN", slot=2, is_odd=False)
        assert data["song"] == "Test Song"
        assert data["ragam"] == "Hindolam"
        assert data["performer_key"] == "KVN"
        assert data["slot"] == 2
        assert "is_odd" not in data
        assert data["local_audio_name"] == local_audio_name(track)

    def test_to_dict_odd_flag(self):
        data = make_track().to_dict(performer_key="DKJ", slot=4, is_odd=True)
        assert data["is_odd"] is True


class TestLoadTracks:
    def test_load_fixture_row_count(self, mini_csv):
        tracks = load_tracks(mini_csv)
        assert len(tracks) == 7

    def test_skips_rows_missing_required_fields(self, tmp_path):
        csv_path = tmp_path / "sparse.csv"
        csv_path.write_text(
            "Trk,Song,Ragam,Musician,ConcertFolder,FileName,RelativePath,Type\n"
            "1,Good,Hindolam,PalghatKVNarayanaswamy,Album-001,a.mp3,p/a,Vocal\n"
            "2,NoMusician,Hindolam,,Album-001,b.mp3,p/b,Vocal\n"
            "3,NoFile,Hindolam,MDRamanathan,Album-001,,p/c,Vocal\n",
            encoding="utf-8",
        )
        assert len(load_tracks(csv_path)) == 1

    def test_builds_relative_path_when_missing(self, tmp_path):
        csv_path = tmp_path / "no_rel.csv"
        csv_path.write_text(
            "Song,Ragam,Musician,ConcertFolder,FileName,Type\n"
            "S,Hindolam,MDRamanathan,Album-001,x.mp3,Vocal\n",
            encoding="utf-8",
        )
        tracks = load_tracks(csv_path)
        assert tracks[0].relative_path == "MDRamanathan/Album-001/x.mp3"

    def test_default_song_name_when_empty(self, tmp_path):
        csv_path = tmp_path / "nosong.csv"
        csv_path.write_text(
            "Song,Ragam,Musician,ConcertFolder,FileName,Type\n"
            ",Hindolam,MDRamanathan,Album-001,x.mp3,Vocal\n",
            encoding="utf-8",
        )
        assert load_tracks(csv_path)[0].song == "?"

    def test_production_csv_loads_thousands_of_tracks(self, production_csv):
        tracks = load_tracks(production_csv)
        assert len(tracks) > 15_000
        vocal = [t for t in tracks if t.track_type == "Vocal"]
        assert len(vocal) > 10_000


class TestLocalPaths:
    def test_local_audio_name_matches_fetch_convention(self):
        track = make_track(file_name="01-A.mp3")
        assert local_audio_name(track) == "PalghatKVNarayanaswamy_Album-018_01-A.mp3"

    def test_local_audio_path_joins_audio_dir(self, tmp_path):
        track = make_track()
        assert local_audio_path(track, tmp_path) == tmp_path / local_audio_name(track)


class TestMusicianMap:
    def test_load_musician_map_returns_dict(self, musicians_path):
        mapping = load_musician_map(musicians_path)
        assert mapping["PalghatKVNarayanaswamy"] == "KVN"
        assert mapping["MDRamanathan"] == "MDR"

    def test_load_missing_file_returns_empty(self, tmp_path):
        assert load_musician_map(tmp_path / "missing.json") == {}

    def test_performer_key_for_unknown_musician(self, musicians_path):
        mapping = load_musician_map(musicians_path)
        assert performer_key_for_musician("UnknownArtist", mapping) is None

    def test_all_musician_map_values_exist_in_performers(self, musicians_path, performers_path):
        mapping = load_musician_map(musicians_path)
        performers = json.loads(performers_path.read_text(encoding="utf-8"))
        for musician, key in mapping.items():
            assert key in performers, f"{musician} maps to missing performer key {key!r}"


class TestFilterEligible:
    def test_empty_when_no_local_files(self, mini_csv, musicians_path, pics_dir, tmp_path):
        tracks = load_tracks(mini_csv)
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        assert filter_eligible(tracks, audio_dir=audio_dir, musician_map=mapping, pics_dir=pics_dir) == []

    def test_excludes_non_vocal(self, musicians_path, pics_dir, tmp_path):
        track = make_track(track_type="Clarinet")
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        (audio_dir / local_audio_name(track)).write_bytes(b"x")
        assert filter_eligible([track], audio_dir=audio_dir, musician_map=mapping, pics_dir=pics_dir) == []

    def test_excludes_ragamalika(self, musicians_path, pics_dir, tmp_path):
        track = make_track(ragam="Ragamalika")
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        (audio_dir / local_audio_name(track)).write_bytes(b"x")
        assert filter_eligible([track], audio_dir=audio_dir, musician_map=mapping, pics_dir=pics_dir) == []

    def test_excludes_empty_ragam(self, musicians_path, pics_dir, tmp_path):
        track = make_track(ragam="")
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        (audio_dir / local_audio_name(track)).write_bytes(b"x")
        assert filter_eligible([track], audio_dir=audio_dir, musician_map=mapping, pics_dir=pics_dir) == []

    def test_excludes_unmapped_musician(self, pics_dir, tmp_path):
        track = make_track(musician="TotallyUnknownMusician")
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        (audio_dir / local_audio_name(track)).write_bytes(b"x")
        assert filter_eligible([track], audio_dir=audio_dir, musician_map={}, pics_dir=pics_dir) == []

    def test_excludes_missing_performer_photo(self, musicians_path, tmp_path):
        track = make_track(musician="PalghatKVNarayanaswamy")
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        (audio_dir / local_audio_name(track)).write_bytes(b"x")
        empty_pics = tmp_path / "Pics"
        empty_pics.mkdir()
        assert filter_eligible([track], audio_dir=audio_dir, musician_map=mapping, pics_dir=empty_pics) == []

    def test_excludes_missing_local_file(self, musicians_path, pics_dir, tmp_path):
        track = make_track()
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        assert filter_eligible([track], audio_dir=audio_dir, musician_map=mapping, pics_dir=pics_dir) == []

    def test_includes_track_when_all_criteria_met(self, musicians_path, pics_dir, tmp_path):
        track = make_track()
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        (audio_dir / local_audio_name(track)).write_bytes(b"x")
        eligible = filter_eligible([track], audio_dir=audio_dir, musician_map=mapping, pics_dir=pics_dir)
        assert len(eligible) == 1
        assert eligible[0].musician == "PalghatKVNarayanaswamy"

    def test_require_local_false_allows_missing_file(self, musicians_path, pics_dir, tmp_path):
        track = make_track()
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        eligible = filter_eligible(
            [track],
            audio_dir=audio_dir,
            musician_map=mapping,
            pics_dir=pics_dir,
            require_local=False,
        )
        assert len(eligible) == 1

    def test_fixture_all_vocal_tracks_when_seeded(self, mini_csv, musicians_path, pics_dir, tmp_path):
        tracks = load_tracks(mini_csv)
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        seeded = seed_mini_audio(audio_dir, mini_csv, mapping)
        eligible = filter_eligible(tracks, audio_dir=audio_dir, musician_map=mapping, pics_dir=pics_dir)
        assert seeded == 6
        assert len(eligible) == 6


class TestGroupByRagam:
    def test_groups_tracks_by_ragam_name(self):
        tracks = [
            make_track(ragam="Hindolam", file_name="a.mp3"),
            make_track(ragam="Hindolam", file_name="b.mp3", musician="MDRamanathan"),
            make_track(ragam="Hamsanandi", file_name="c.mp3", musician="DKJayaraman"),
        ]
        grouped = group_by_ragam(tracks)
        assert len(grouped["Hindolam"]) == 2
        assert len(grouped["Hamsanandi"]) == 1


class TestProductionDataIntegrity:
    def test_excluded_ragams_not_empty(self):
        assert "Ragamalika" in EXCLUDED_RAGAMS

    def test_production_pairs_reference_ragams_in_csv(self, production_csv, production_pairs):
        from select_quiz_tracks import load_ragam_pairs

        tracks = load_tracks(production_csv)
        ragams_in_csv = {t.ragam for t in tracks if t.ragam}
        pairs = load_ragam_pairs(production_pairs)
        for pair in pairs:
            assert pair.main in ragams_in_csv, f"Main ragam {pair.main!r} not in CSV"
            assert pair.odd in ragams_in_csv, f"Odd ragam {pair.odd!r} not in CSV"

    def test_production_has_vocal_tracks_for_common_pairs(self, production_csv, production_pairs):
        from select_quiz_tracks import load_ragam_pairs

        tracks = load_tracks(production_csv)
        vocal_by_ragam = group_by_ragam([t for t in tracks if t.track_type == "Vocal" and t.ragam])
        pairs = load_ragam_pairs(production_pairs)
        # At least the three quiz example pairs should have enough catalog depth
        for main, odd in [("Hindolam", "Hamsanandi"), ("Kambhoji", "Harikambhoji"), ("Kharaharapriya", "Bhairavi")]:
            assert len(vocal_by_ragam.get(main, [])) >= 3
            assert len(vocal_by_ragam.get(odd, [])) >= 1
        assert len(pairs) >= 3

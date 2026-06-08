"""Tests for select_quiz_tracks.py — selection logic and CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from music_index import load_musician_map, load_tracks, local_audio_name
from select_quiz_tracks import (
    QuizSelection,
    format_selection,
    load_ragam_pairs,
    sample_main_tracks,
    select_quiz_tracks,
    valid_pairs,
)
from tests.conftest import assert_valid_selection, make_track, seed_mini_audio

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PYTHON = ROOT / ".venv" / "bin" / "python"
SCRIPT = ROOT / "select_quiz_tracks.py"


class TestLoadRagamPairs:
    def test_loads_fixture_pairs(self, mini_pairs):
        pairs = load_ragam_pairs(mini_pairs)
        assert len(pairs) == 2
        assert pairs[0].main == "Hindolam"
        assert pairs[0].odd == "Hamsanandi"

    def test_loads_production_pairs(self, production_pairs):
        pairs = load_ragam_pairs(production_pairs)
        assert len(pairs) >= 20


class TestValidPairs:
    def test_returns_only_pairs_with_enough_tracks(self, mini_pairs):
        pairs = load_ragam_pairs(mini_pairs)
        by_ragam = {
            "Hindolam": [object()] * 3,
            "Hamsanandi": [object()],
            "Kambhoji": [object()] * 2,
        }
        result = valid_pairs(pairs, by_ragam)
        assert len(result) == 1
        assert result[0].main == "Hindolam"

    def test_requires_exactly_three_for_main(self, mini_pairs):
        pairs = load_ragam_pairs(mini_pairs)
        by_ragam = {"Hindolam": [object()] * 2, "Hamsanandi": [object()]}
        assert valid_pairs(pairs, by_ragam) == []

    def test_requires_at_least_one_odd_track(self, mini_pairs):
        pairs = load_ragam_pairs(mini_pairs)
        by_ragam = {"Hindolam": [object()] * 3, "Hamsanandi": []}
        assert valid_pairs(pairs, by_ragam) == []


class TestSampleMainTracks:
    def test_prefers_distinct_musicians(self):
        tracks = [
            make_track(musician="PalghatKVNarayanaswamy", file_name="a.mp3"),
            make_track(musician="MDRamanathan", file_name="b.mp3"),
            make_track(musician="GNBalasubramaniam", file_name="c.mp3"),
            make_track(musician="PalghatKVNarayanaswamy", file_name="d.mp3", concert_folder="Album-025"),
        ]
        picked = sample_main_tracks(tracks, 3)
        assert len(picked) == 3
        assert len({t.musician for t in picked}) == 3

    def test_falls_back_when_fewer_than_three_musicians(self):
        tracks = [
            make_track(musician="PalghatKVNarayanaswamy", file_name=f"{i}.mp3", concert_folder=f"Album-{i}")
            for i in range(4)
        ]
        picked = sample_main_tracks(tracks, 3)
        assert len(picked) == 3

    def test_raises_when_insufficient_tracks(self):
        with pytest.raises(ValueError, match="Need at least 3"):
            sample_main_tracks([make_track()], 3)


class TestSelectQuizTracks:
    def test_seed_reproducibility(self, mini_csv, mini_pairs, musicians_path, pics_dir, tmp_path):
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        seed_mini_audio(audio_dir, mini_csv, mapping)

        first = select_quiz_tracks(
            csv_path=mini_csv,
            pairs_path=mini_pairs,
            musicians_path=musicians_path,
            audio_dir=audio_dir,
            pics_dir=pics_dir,
            seed=42,
        )
        second = select_quiz_tracks(
            csv_path=mini_csv,
            pairs_path=mini_pairs,
            musicians_path=musicians_path,
            audio_dir=audio_dir,
            pics_dir=pics_dir,
            seed=42,
        )
        assert first.main_ragam == second.main_ragam
        assert [t.file_name for t in first.main_tracks] == [t.file_name for t in second.main_tracks]
        assert first.odd_track.file_name == second.odd_track.file_name

    def test_selection_passes_validation(self, mini_csv, mini_pairs, musicians_path, pics_dir, tmp_path):
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        seed_mini_audio(audio_dir, mini_csv, mapping)

        selection = select_quiz_tracks(
            csv_path=mini_csv,
            pairs_path=mini_pairs,
            musicians_path=musicians_path,
            audio_dir=audio_dir,
            pics_dir=pics_dir,
            seed=99,
        )
        assert_valid_selection(selection, mapping, mini_pairs, audio_dir, pics_dir=pics_dir)
        assert selection.main_ragam == "Hindolam"
        assert selection.odd_ragam == "Hamsanandi"

    def test_different_seeds_can_differ(self, mini_csv, mini_pairs, musicians_path, pics_dir, tmp_path):
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        seed_mini_audio(audio_dir, mini_csv, mapping)

        results = set()
        for seed in range(20):
            sel = select_quiz_tracks(
                csv_path=mini_csv,
                pairs_path=mini_pairs,
                musicians_path=musicians_path,
                audio_dir=audio_dir,
                pics_dir=pics_dir,
                seed=seed,
            )
            key = tuple(t.file_name for t in sel.main_tracks) + (sel.odd_track.file_name,)
            results.add(key)
        assert len(results) > 1, "Expected different seeds to produce different track picks"

    def test_exits_when_no_valid_pairs(self, mini_csv, mini_pairs, musicians_path, pics_dir, tmp_path):
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        with pytest.raises(SystemExit, match="No valid ragam pairs"):
            select_quiz_tracks(
                csv_path=mini_csv,
                pairs_path=mini_pairs,
                musicians_path=musicians_path,
                audio_dir=audio_dir,
                pics_dir=pics_dir,
                seed=1,
            )


class TestQuizSelection:
    def test_to_dict_structure(self):
        main = make_track(song="A", file_name="a.mp3")
        odd = make_track(song="E", ragam="Hamsanandi", musician="DKJayaraman", file_name="e.mp3")
        selection = QuizSelection("Hindolam", "Hamsanandi", [main, main, main], odd, seed=7)
        mapping = {"PalghatKVNarayanaswamy": "KVN", "DKJayaraman": "DKJ"}
        data = selection.to_dict(mapping)
        assert data["seed"] == 7
        assert len(data["clips"]) == 4
        assert data["clips"][3]["is_odd"] is True
        assert data["clips"][0]["performer_key"] == "KVN"
        assert data["clips"][3]["performer_key"] == "DKJ"

    def test_format_selection_includes_ragams_and_paths(self, musicians_path):
        main = make_track(song="Raamanukku", file_name="a.mp3")
        odd = make_track(song="Niraimadi", ragam="Hamsanandi", musician="DKJayaraman", file_name="e.mp3")
        selection = QuizSelection("Hindolam", "Hamsanandi", [main, main, main], odd, seed=42)
        mapping = load_musician_map(musicians_path)
        text = format_selection(selection, mapping)
        assert "Main ragam: Hindolam" in text
        assert "Odd ragam:  Hamsanandi" in text
        assert "Seed: 42" in text
        assert "gs://mwappv1-carnatic/" in text
        assert "[ODD]" in text


class TestCLI:
    def test_cli_json_output_valid(self, mini_csv, mini_pairs, musicians_path, pics_dir, tmp_path):
        if not PYTHON.is_file():
            pytest.skip("venv not present")
        mapping = load_musician_map(musicians_path)
        audio_dir = tmp_path / "audio-clips"
        audio_dir.mkdir()
        seed_mini_audio(audio_dir, mini_csv, mapping)

        proc = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT),
                "--csv", str(mini_csv),
                "--pairs", str(mini_pairs),
                "--musicians", str(musicians_path),
                "--audio-dir", str(audio_dir),
                "--pics-dir", str(pics_dir),
                "--seed", "42",
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert data["main_ragam"] == "Hindolam"
        assert data["odd_ragam"] == "Hamsanandi"
        assert len(data["clips"]) == 4
        assert data["seed"] == 42

    def test_cli_fails_without_local_audio(self, mini_csv, mini_pairs, musicians_path, pics_dir, tmp_path):
        if not PYTHON.is_file():
            pytest.skip("venv not present")
        audio_dir = tmp_path / "empty"
        audio_dir.mkdir()
        proc = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT),
                "--csv", str(mini_csv),
                "--pairs", str(mini_pairs),
                "--musicians", str(musicians_path),
                "--audio-dir", str(audio_dir),
                "--pics-dir", str(pics_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        assert proc.returncode != 0
        assert "No valid ragam pairs" in proc.stderr or "No valid ragam pairs" in proc.stdout

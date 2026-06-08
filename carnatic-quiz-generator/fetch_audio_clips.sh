#!/usr/bin/env bash
# Download starter source albums from GCS into audio-clips/.
# These albums support the Hindolam/Hamsanandi pair in ragam_pairs.json
# once tracks are matched via MasterWebAppMusicIndex.csv.
# Requires: gsutil with access to gs://mwappv1-carnatic (bucket is private).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

fetch_album() {
  "$ROOT/fetch_album.sh" "$1" "$2"
}

echo "Fetching starter albums for quiz track selection ..."
fetch_album PalghatKVNarayanaswamy Album-018
fetch_album MDRamanathan Album-001
fetch_album GNBalasubramaniam Album-007
fetch_album DKJayaraman Album-003

echo ""
echo "Done. $(ls -1 "$ROOT/audio-clips"/*.mp3 2>/dev/null | wc -l | tr -d ' ') MP3(s) in $ROOT/audio-clips"
echo "Run: .venv/bin/python select_quiz_tracks.py"

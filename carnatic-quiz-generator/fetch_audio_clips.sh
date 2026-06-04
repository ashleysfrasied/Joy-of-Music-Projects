#!/usr/bin/env bash
# Download AKC Natarajan Album-001 source MP3s from GCS into audio-clips/.
# Requires: gsutil with access to gs://mwappv1-carnatic (bucket is private).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/audio-clips"
GCS_PREFIX="gs://mwappv1-carnatic/AKCNatarajan/Album-001"
LOCAL_PREFIX="AKCNatarajan_Album-001"

mkdir -p "$DEST"

echo "Downloading from $GCS_PREFIX to $DEST ..."
for obj in $(gsutil ls "${GCS_PREFIX}/*.mp3"); do
  base="$(basename "$obj")"
  local_name="${LOCAL_PREFIX}_${base}"
  echo "  $base -> $local_name"
  gsutil cp "$obj" "$DEST/$local_name"
done

echo "Done. $(ls -1 "$DEST"/*.mp3 2>/dev/null | wc -l | tr -d ' ') MP3(s) in $DEST"

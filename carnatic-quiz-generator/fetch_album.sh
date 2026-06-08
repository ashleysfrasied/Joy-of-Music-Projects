#!/usr/bin/env bash
# Download one album from GCS into audio-clips/ using CSV naming convention.
# Usage: ./fetch_album.sh <Musician> <ConcertFolder>
# Example: ./fetch_album.sh PalghatKVNarayanaswamy Album-018
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <Musician> <ConcertFolder>" >&2
  echo "Example: $0 PalghatKVNarayanaswamy Album-018" >&2
  exit 1
fi

MUSICIAN="$1"
CONCERT="$2"
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/audio-clips"
GCS_PREFIX="gs://mwappv1-carnatic/${MUSICIAN}/${CONCERT}"
LOCAL_PREFIX="${MUSICIAN}_${CONCERT}"

mkdir -p "$DEST"

echo "Downloading from $GCS_PREFIX to $DEST ..."
count=0
for obj in $(gsutil ls "${GCS_PREFIX}/*.mp3" 2>/dev/null || true); do
  base="$(basename "$obj")"
  local_name="${LOCAL_PREFIX}_${base}"
  echo "  $base -> $local_name"
  gsutil cp "$obj" "$DEST/$local_name"
  count=$((count + 1))
done

if [[ "$count" -eq 0 ]]; then
  echo "No MP3s found at $GCS_PREFIX" >&2
  exit 1
fi

echo "Done. $count MP3(s) downloaded."

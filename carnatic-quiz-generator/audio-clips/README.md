# Source audio

Full-length concert recordings used to extract ~30 second quiz clips. **Do not edit these files in place** — trim copies into the target `Quiz*` folder instead.

MP3s are **not committed to git** (too large). Download them locally with the fetch script (see below).

## Download local copies

From `carnatic-quiz-generator/`:

```bash
./fetch_audio_clips.sh
```

Requires [gsutil](https://cloud.google.com/storage/docs/gsutil) and authenticated access to bucket `mwappv1-carnatic`.

List what you have locally:

```bash
ls audio-clips/*.mp3
```

## Upstream (Google Cloud Storage)

Console: [mwappv1-carnatic / AKCNatarajan / Album-001](https://console.cloud.google.com/storage/browser/mwappv1-carnatic/AKCNatarajan/Album-001;tab=objects?prefix=&forceOnObjectsSortingFiltering=false)

**GCS object names** (as stored in the bucket):

```text
gs://mwappv1-carnatic/AKCNatarajan/Album-001/01-SreeMahaaganapatiravatuMaam.mp3
gs://mwappv1-carnatic/AKCNatarajan/Album-001/02-Gaanamoorte.mp3
…
```

**Local names after fetch** — `fetch_audio_clips.sh` prefixes each object with the album id so multiple albums can share `audio-clips/`:

```text
AKCNatarajan_Album-001_01-SreeMahaaganapatiravatuMaam.mp3
AKCNatarajan_Album-001_02-Gaanamoorte.mp3
…
```

## Ragam selection

Ragam metadata for quiz prep lives in the **Excel spreadsheet** (see `automation-process.md`), not in this folder. Use the spreadsheet to pick ragam pairs and match tracks; use `audio-clips/` only for the full-length source files to trim from.

## Adding more albums

Keep all source MP3s **flat in `audio-clips/`** (no subfolders). Use a distinct filename prefix per album so files from different albums do not collide:

1. Extend `fetch_audio_clips.sh` (or add a sibling script) for the new GCS prefix.
2. Set a unique `LOCAL_PREFIX` (e.g. `Performer_Album-002`).
3. Add the performer to `performers.json` and a photo under `Pics/` if needed.

## Rights and usage

These recordings are project-licensed source material stored in a private GCS bucket (`mwappv1-carnatic`). Use them only for Carnatic quiz video production within this project. Do not redistribute or publish the full-length source files outside the team workflow.

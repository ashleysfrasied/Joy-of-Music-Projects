# Source audio

Full-length concert recordings used to extract ~30 second quiz clips. **Do not edit these files in place** — trim copies into the target `Quiz*` folder instead.

MP3s are **not committed to git** (too large). Download them locally with the fetch scripts (see below).

## Download local copies

From `carnatic-quiz-generator/`:

```bash
./fetch_audio_clips.sh
```

This fetches starter albums that support the **Hindolam / Hamsanandi** pair in `ragam_pairs.json` (KVN, MDR, GNB, DKJ albums).

Fetch a specific album:

```bash
./fetch_album.sh PalghatKVNarayanaswamy Album-018
./fetch_album.sh MDRamanathan Album-001
```

Requires [gsutil](https://cloud.google.com/storage/docs/gsutil) and authenticated access to bucket `mwappv1-carnatic`.

List what you have locally:

```bash
ls audio-clips/*.mp3
```

Then select quiz tracks:

```bash
.venv/bin/python select_quiz_tracks.py
```

## Upstream (Google Cloud Storage)

Console: [mwappv1-carnatic](https://console.cloud.google.com/storage/browser/mwappv1-carnatic;tab=objects)

**GCS object path** (from `MasterWebAppMusicIndex.csv` column `RelativePath`):

```text
gs://mwappv1-carnatic/PalghatKVNarayanaswamy/Album-018/07-RaamanukkuMannanMudi.mp3
```

**Local names after fetch** — `{Musician}_{ConcertFolder}_{FileName}`:

```text
PalghatKVNarayanaswamy_Album-018_07-RaamanukkuMannanMudi.mp3
```

## Ragam selection

Ragam metadata lives in **`MasterWebAppMusicIndex.csv`**. Run `select_quiz_tracks.py` to randomly pick a similar pair from `ragam_pairs.json` and choose 3+1 local vocal tracks. Selection requires:

- Source MP3 present in `audio-clips/`
- `Type == Vocal` in the CSV
- Musician mapped in `musicians.json` with a photo in `Pics/`

If selection fails with “No valid ragam pairs”, fetch more albums for a pair listed in `ragam_pairs.json`. Examples for other pairs:

```bash
./fetch_album.sh PalghatKVNarayanaswamy Album-096   # Kambhoji
./fetch_album.sh SemmangudiDrRSrinivasaIyer Album-003  # Harikambhoji
./fetch_album.sh MaduraiSSomasundaram Album-003     # Kharaharapriya
./fetch_album.sh RamnadKrishnan Album-010           # Bhairavi
```

## Adding more albums

Keep all source MP3s **flat in `audio-clips/`** (no subfolders). Use `fetch_album.sh` with the `Musician` and `ConcertFolder` values from `MasterWebAppMusicIndex.csv`.

1. Run `./fetch_album.sh <Musician> <ConcertFolder>`.
2. Add the musician to `musicians.json` and `performers.json` if needed.
3. Add a photo under `Pics/` if needed.

## Rights and usage

These recordings are project-licensed source material stored in a private GCS bucket (`mwappv1-carnatic`). Use them only for Carnatic quiz video production within this project. Do not redistribute or publish the full-length source files outside the team workflow.

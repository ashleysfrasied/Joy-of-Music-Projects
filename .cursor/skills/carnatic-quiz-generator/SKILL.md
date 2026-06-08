---
name: carnatic-quiz-generator
description: >-
  Builds Carnatic "find the odd one out" quiz teaching videos from four MP3
  clips, performer photos, and quiz-text.md. Use when the user says
  carnatic-quiz-generator, build quiz video, make a quiz video, prepare a new
  quiz folder, or work in carnatic-quiz-generator.
---

# carnatic-quiz-generator

## Working directory

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/carnatic-quiz-generator"
```

## Build video (automated)

1. `cd` to `carnatic-quiz-generator/` (see above).
2. If `.venv` is missing: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. Confirm **ffmpeg** is on `PATH` (`ffmpeg -version`).
4. Confirm the quiz folder has **exactly four** `.mp3` files and `quiz-text.md` (four non-empty lines for the intro slide).
5. Run:

```bash
.venv/bin/python build_quiz_video.py --quiz-dir Quiz39
```

Use the target folder name instead of `Quiz39`. Optional: `--seed 42` for reproducible clip order.

6. Report the output folder (default: `completed-videos/Quiz{N}/` containing `Quiz{N}_video.mp4`, `quiz-text.md`, and `quiz-answer.md`).

### Audio naming

Prefer `PerformerKey-Ragam.mp3` (hyphen before ragam). The prefix must exist in `performers.json` and match a photo in `Pics/` (fuzzy filename match). Avoid underscore-only stems (e.g. `MSS_Kharaharapriya.mp3`) — parsing is unreliable.

### Intro copy (`quiz-text.md`)

Example:

```markdown
Three of the four clips are in the same ragam.
Find the odd one out
Carnatic Quiz #39
Question 2
```

Line 2 highlights **odd** on the intro slide.

## Source audio

Full-length recordings for clip extraction are in **`audio-clips/`** (downloaded from GCS bucket `mwappv1-carnatic` — not in git). See `audio-clips/README.md`.

```bash
./fetch_audio_clips.sh
ls audio-clips/*.mp3
```

Never edit originals in `audio-clips/` — trim copies into the quiz folder.

## Select tracks (automated)

```bash
./fetch_audio_clips.sh   # if audio-clips/ is empty or selection fails
.venv/bin/python select_quiz_tracks.py [--seed 42] [--json]
```

Uses `MasterWebAppMusicIndex.csv`, `ragam_pairs.json`, and `musicians.json`. Picks a random similar ragam pair with 3 local vocal tracks from the main ragam and 1 from the odd ragam. **Only artists with a matching photo in `Pics/` are eligible** — tracks without a performer image are skipped. Clip 4 is always the odd ragam.

## Prepare a new quiz (partially automated)

Follow `carnatic-quiz-generator/automation-process.md`:

1. Run **`select_quiz_tracks.py`** (steps above).
2. Extract ~**30 seconds** per clip with **vocal** content from the listed local source files; label working files clip1–clip4 where **clip4 is always the odd ragam**.
4. **Checkpoint after each clip** — confirm the segment before continuing.
5. Create the next numbered folder: `Quiz42`, `Quiz43`, … (scan existing `Quiz*` folders for the highest number + 1).
6. Place in that folder:
   - Four final `.mp3` files (renamed to `PerformerKey-Ragam.mp3`)
   - `quiz-text.md` (quiz number and question index on lines 3–4)
   - Optional metadata listing artist, ragam, and source file per clip
7. Add unknown performers to `performers.json` and `Pics/` before building the video.
8. Run **Build video** above.

## Rules

- Never delete or overwrite an existing file in `completed-videos/` without explicit user approval.
- Do not change source recordings in place; copy trimmed clips into the quiz folder.
- Three clips must share one ragam; the fourth must be the similar “odd” ragam (not random unrelated ragams).

## Troubleshooting

| Issue | Action |
|-------|--------|
| `Expected exactly 4 mp3 files` | Quiz folder must contain exactly four MP3s |
| `No picture found for performer key` | Add or rename a file under `Pics/` |
| `ffmpeg failed` | Install ffmpeg; verify MP3s play |
| Wrong on-screen name | Fix key in `performers.json` |
| `No valid ragam pairs` | Run `./fetch_audio_clips.sh` or `./fetch_album.sh <Musician> <ConcertFolder>` |

## Reference

- CLI flags and layout: `carnatic-quiz-generator/README.md`
- Full Ashley workflow spec: `carnatic-quiz-generator/automation-process.md`

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

6. Report the output path (default: `<quiz-dir>/<folder>_video.mp4`, e.g. `Quiz39/Quiz39_video.mp4`).

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

## Prepare a new quiz (manual — not scripted yet)

Follow `carnatic-quiz-generator/automation-process.md` until spreadsheet/clip automation exists:

1. Pick **two ragams** that differ by only one or two notes (subtle “odd one out”).
2. Choose **3** audio sources from one ragam and **1** from the other (random pair each run).
3. Extract ~**30 seconds** per clip with **vocal** content; label working files clip1–clip4 where **clip4 is always the odd ragam**.
4. **Checkpoint after each clip** — confirm the segment before continuing.
5. Create the next numbered folder: `Quiz42`, `Quiz43`, … (scan existing `Quiz*` folders for the highest number + 1).
6. Place in that folder:
   - Four final `.mp3` files (renamed to `PerformerKey-Ragam.mp3`)
   - `quiz-text.md` (quiz number and question index on lines 3–4)
   - Optional metadata listing artist, ragam, and source file per clip
7. Add unknown performers to `performers.json` and `Pics/` before building the video.
8. Run **Build video** above.

## Rules

- Never delete or overwrite an existing `*_video.mp4` without explicit user approval.
- Do not change source recordings in place; copy trimmed clips into the quiz folder.
- Three clips must share one ragam; the fourth must be the similar “odd” ragam (not random unrelated ragams).

## Troubleshooting

| Issue | Action |
|-------|--------|
| `Expected exactly 4 mp3 files` | Quiz folder must contain exactly four MP3s |
| `No picture found for performer key` | Add or rename a file under `Pics/` |
| `ffmpeg failed` | Install ffmpeg; verify MP3s play |
| Wrong on-screen name | Fix key in `performers.json` |

## Reference

- CLI flags and layout: `carnatic-quiz-generator/README.md`
- Full Ashley workflow spec: `carnatic-quiz-generator/automation-process.md`

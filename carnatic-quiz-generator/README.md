# Carnatic Quiz Video Generator

Builds **“find the odd one out”** teaching videos for Carnatic music: an intro slide plus four audio clips, each paired with a performer photo.

Three clips share one ragam; the fourth is from a similar ragam. The video shuffles clip order so listeners must identify which performance does not belong.

## Invoke in Cursor / Claude

Project skill: **`.cursor/skills/carnatic-quiz-generator/`** (mirrored in `.claude/skills/carnatic-quiz-generator/`).

```text
/carnatic-quiz-generator
```

Or say: “build a quiz video” or “prepare a new quiz folder”.

## Prerequisites

- **Python 3.10+**
- **ffmpeg** on your `PATH` (`ffmpeg -version` to check)

## Quick start

```bash
cd carnatic-quiz-generator
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build_quiz_video.py --quiz-dir Quiz39
```

Output: `Quiz39/Quiz39_video.mp4`

Use `--seed 42` for a reproducible clip order.

## What each quiz folder needs

| File | Purpose |
|------|---------|
| **4 × `.mp3`** | One clip per performer/ragam (see naming below) |
| **`quiz-text.md`** | Intro copy rendered on the opening slide (4 non-empty lines) |

Example intro (`Quiz39/quiz-text.md`):

```markdown
Three of the four clips are in the same ragam.
Find the odd one out
Carnatic Quiz #39
Question 2
```

Line 2 highlights the word **odd** in black on the intro slide.

## Audio file naming

Use a **performer key** before the first hyphen, then the ragam:

```text
KVN-Hindolam.mp3
Lalgudi-Hindolam.mp3
MSG-Hamsanandi.mp3
```

The script reads the prefix (`KVN`, `Lalgudi`, …) to:

1. Look up the display name in `performers.json`
2. Match a photo in `Pics/` (fuzzy match on filename)

Prefer hyphens (`Performer-Ragam.mp3`). Underscore-only names (e.g. `MSS_Kharaharapriya.mp3`) are not parsed reliably today.

## Shared assets

| Path | Purpose |
|------|---------|
| `Pics/` | Performer photos (`.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`) |
| `performers.json` | Maps short keys to full display names on clip slides |
| `intro-background.jpg` | Background for the intro slide |

Add new performers to `performers.json` and drop a matching image into `Pics/` before building a quiz that uses them.

## CLI options

```bash
.venv/bin/python build_quiz_video.py --help
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--quiz-dir` | `Quiz39` | Folder with MP3s and `quiz-text.md` |
| `--assets-dir` | project root | Location of `Pics/`, `performers.json`, intro background |
| `--output` | `<quiz-dir>/<name>_video.mp4` | Output video path |
| `--intro-duration` | `8.0` | Intro length in seconds |
| `--clip-max-duration` | `30.0` | Max seconds per clip (audio trimmed if longer) |
| `--seed` | (random) | Fixed seed for clip shuffle order |
| `--intro-bg` | `intro-background.jpg` | Override intro background image |

## Project layout

```text
carnatic-quiz-generator/
├── build_quiz_video.py      # Video builder (implemented)
├── automation-process.md    # Full workflow spec (partially automated)
├── performers.json
├── intro-background.jpg
├── Pics/                    # Performer photos
├── Quiz39/                  # Example: complete quiz + video
├── Quiz40/                  # MP3s only (no video yet)
├── Quiz41/
└── requirements.txt
```

## Planned workflow

See `automation-process.md` for the end-to-end process Ashley described. **Implemented today:** step 10 (video from four clips + artist images) and step 11 (`quiz-text.md` maps filenames to artist names via `performers.json`).

**Not yet automated:**

- Picking ragam pairs from a spreadsheet (similar ragams, 3+1 clip selection)
- Extracting ~30s vocal segments from source recordings
- Human approval checkpoints per clip
- Auto-creating numbered quiz folders and metadata files

Until those steps exist, prepare each quiz folder manually (four MP3s + `quiz-text.md`), then run `build_quiz_video.py`.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Expected exactly 4 mp3 files` | Add or remove MP3s so the quiz folder has exactly four |
| `No picture found for performer key` | Add a photo to `Pics/` whose filename matches the audio prefix |
| `ffmpeg failed` | Install ffmpeg or check that MP3 files are valid |
| Wrong name on slide | Add or fix the key in `performers.json` |

#!/usr/bin/env python3
"""
Build a single-quiz teaching video: intro (from quiz-text.md + intro-background)
plus four audio/image pairs in random order. Requires ffmpeg on PATH.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    from mutagen.mp3 import MP3
except ImportError as e:
    raise SystemExit("Install dependencies: pip install -r requirements.txt") from e

CANVAS_W = 1920
CANVAS_H = 1080
FPS = 30
ACCENT = (220, 85, 40)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
# Lower-third: dark bar + light text (readable on any photo)
BAR_RGBA = (18, 20, 26, 238)
TEXT_LABEL = (168, 174, 188)
TEXT_NAME = (248, 248, 252)
CLIP_MAX_DURATION_SEC = 30.0
AUDIO_RATE = 48000
AUDIO_CHANNELS = 2
COMPLETED_VIDEOS_DIRNAME = "completed-videos"
COMPLETED_QUIZ_DIR_RE = re.compile(r"^Quiz(\d+)$", re.IGNORECASE)
COMPLETED_VIDEO_RE = re.compile(r"^Quiz(\d+)_video\.mp4$", re.IGNORECASE)
QUIZ_TEXT_FILENAMES = (
    "quiz-text.md",
    "Quiz-Text.md",
    "QuixText.md",
    "QuizText.md",
)


def normalize_stem(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def next_completed_quiz_output(completed_dir: Path) -> tuple[Path, Path, int]:
    """Return (quiz_dir, video_path, quiz_number) under completed-videos/."""
    completed_dir.mkdir(parents=True, exist_ok=True)
    highest = 0
    for path in completed_dir.iterdir():
        if path.is_dir():
            match = COMPLETED_QUIZ_DIR_RE.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
        elif path.is_file():
            match = COMPLETED_VIDEO_RE.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    quiz_num = highest + 1
    quiz_dir = completed_dir / f"Quiz{quiz_num}"
    return quiz_dir, quiz_dir / f"Quiz{quiz_num}_video.mp4", quiz_num


def next_completed_video_path(completed_dir: Path) -> Path:
    """Legacy helper — returns the video path inside the next quiz folder."""
    _, video_path, _ = next_completed_quiz_output(completed_dir)
    return video_path


def load_performers(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def performer_key_from_audio(audio_path: Path) -> str:
    return audio_path.stem.split("-")[0]


def ragam_from_audio(audio_path: Path) -> str:
    stem = audio_path.stem
    if "-" in stem:
        return stem.split("-", 1)[1]
    return stem


def score_image_match(key: str, pic_path: Path) -> tuple[int, int, int] | None:
    """Lower tuple sorts earlier = better. Returns None if no match."""
    ext = pic_path.suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return None
    k = normalize_stem(key)
    s = normalize_stem(pic_path.stem)
    if not k or not s:
        return None
    ext_rank = 0 if ext in {".jpg", ".jpeg", ".webp"} else 1 if ext == ".png" else 2
    if s == k:
        return (0, ext_rank, len(pic_path.stem))
    if s.startswith(k):
        return (1, len(s), ext_rank)
    if k in s:
        return (2, len(s), ext_rank)
    return None


def find_performer_image(pics_dir: Path, key: str) -> Path:
    best: tuple[tuple, Path] | None = None
    for p in pics_dir.iterdir():
        if not p.is_file():
            continue
        sc = score_image_match(key, p)
        if sc is None:
            continue
        if best is None or sc < best[0]:
            best = (sc, p)
    if best is None:
        raise FileNotFoundError(
            f"No picture found for performer key {key!r} under {pics_dir}"
        )
    return best[1]


def _truetype(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont | None:
    if not Path(path).is_file():
        return None
    try:
        return ImageFont.truetype(path, size=size, index=index)
    except OSError:
        return None


def resolve_font_bold(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Intro slides — bold sans."""
    for path, idx in (
        ("/System/Library/Fonts/SFNS.ttf", 0),
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
        ("/System/Library/Fonts/HelveticaNeue.ttc", 8),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),
    ):
        f = _truetype(path, size, idx)
        if f is not None:
            return f
    return ImageFont.load_default()


def resolve_clip_fonts(
    label_px: int, name_px: int
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    """Clip lower-third: clean system UI / neo-grotesque style where available."""
    pairs = (
        ("/System/Library/Fonts/SFNS.ttf", 0, "/System/Library/Fonts/SFNS.ttf", 0),
        (
            "/System/Library/Fonts/HelveticaNeue.ttc",
            5,
            "/System/Library/Fonts/HelveticaNeue.ttc",
            8,
        ),
        (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            0,
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            0,
        ),
    )
    for lp, li, np, ni in pairs:
        lf = _truetype(lp, label_px, li)
        nf = _truetype(np, name_px, ni)
        if lf is not None and nf is not None:
            return lf, nf
    return resolve_font_bold(label_px), resolve_font_bold(name_px)


def load_static_image_rgb(path: Path) -> Image.Image:
    img = Image.open(path)
    if getattr(img, "n_frames", 1) > 1:
        img.seek(0)
    return ImageOps.exif_transpose(img).convert("RGB")


def crop_cover_16_9(img: Image.Image, out_w: int, out_h: int) -> Image.Image:
    """Crop from center to 16:9 then resize to out_w x out_h."""
    w, h = img.size
    target_ratio = out_w / out_h
    cur_ratio = w / h
    if cur_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        cropped = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        cropped = img.crop((0, top, w, top + new_h))
    return cropped.resize((out_w, out_h), Image.Resampling.LANCZOS)


def draw_text_center_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    anchor: str = "mm",
) -> None:
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0), anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)


def draw_intro_slide(
    bg_path: Path,
    lines: list[str],
    out_png: Path,
) -> None:
    bg = load_static_image_rgb(bg_path)
    bg = crop_cover_16_9(bg, CANVAS_W, CANVAS_H)
    draw = ImageDraw.Draw(bg)
    font_large = resolve_font_bold(52)
    font_small = resolve_font_bold(44)
    font_bottom = resolve_font_bold(48)

    if len(lines) >= 1:
        draw_text_center_shadow(
            draw, (CANVAS_W / 2, CANVAS_H * 0.14), lines[0], font_large, ACCENT
        )
    if len(lines) >= 2:
        mid = lines[1]
        m = re.search(r"(?i)\b(odd)\b", mid)
        if m:
            pre, hit, post = mid[: m.start()], mid[m.start() : m.end()], mid[m.end() :]
            parts: list[tuple[str, tuple[int, int, int]]] = []
            if pre.strip():
                parts.append((pre, ACCENT))
            parts.append((hit, BLACK))
            if post.strip():
                parts.append((post, ACCENT))
            total_w = sum(font_large.getlength(t) for t, _ in parts)
            x = (CANVAS_W - total_w) / 2
            y = CANVAS_H * 0.45
            for t, col in parts:
                w = font_large.getlength(t)
                draw_text_center_shadow(draw, (x + w / 2, y), t, font_large, col, anchor="mm")
                x += w
        else:
            draw_text_center_shadow(
                draw, (CANVAS_W / 2, CANVAS_H * 0.45), mid, font_large, ACCENT
            )

    if len(lines) >= 3:
        draw_text_center_shadow(
            draw, (CANVAS_W / 2, CANVAS_H * 0.78), lines[2], font_bottom, ACCENT
        )
    if len(lines) >= 4:
        draw_text_center_shadow(
            draw, (CANVAS_W / 2, CANVAS_H * 0.88), lines[3], font_bottom, ACCENT
        )

    bg.save(out_png, format="PNG")


def pillarbox_slide(performer_img: Image.Image) -> Image.Image:
    """Fit image by height, center on black 16:9 canvas."""
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), (0, 0, 0))
    iw, ih = performer_img.size
    scale = CANVAS_H / ih
    nw = max(1, int(iw * scale))
    resized = performer_img.resize((nw, CANVAS_H), Image.Resampling.LANCZOS)
    x0 = (CANVAS_W - nw) // 2
    canvas.paste(resized, (x0, 0))
    return canvas


def draw_text_lower_third(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    anchor: str = "mm",
) -> None:
    """Subtle depth on dark bars — no heavy outline."""
    x, y = xy
    shadow = (12, 14, 20)
    for dx, dy in ((1, 1), (0, 1), (1, 0)):
        draw.text((x + dx, y + dy), text, font=font, fill=shadow, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)


def draw_clip_slide(
    performer_path: Path,
    clip_index: int,
    display_name: str,
    out_png: Path,
) -> None:
    pic = load_static_image_rgb(performer_path)
    slide = pillarbox_slide(pic)
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    bar_h = max(160, int(CANVAS_H * 0.15))
    y0 = CANVAS_H - bar_h
    od.rectangle((0, y0, CANVAS_W, CANVAS_H), fill=BAR_RGBA)
    slide_rgba = slide.convert("RGBA")
    composed = Image.alpha_composite(slide_rgba, overlay)
    final = composed.convert("RGB")
    draw = ImageDraw.Draw(final)
    font_label, font_name = resolve_clip_fonts(30, 40)
    cx = CANVAS_W / 2
    label_text = f"Clip {clip_index}"
    # Vertically balance label + name inside the bar
    cy1 = y0 + int(bar_h * 0.34)
    cy2 = y0 + int(bar_h * 0.70)
    draw_text_lower_third(draw, (cx, cy1), label_text, font_label, TEXT_LABEL)
    draw_text_lower_third(draw, (cx, cy2), display_name, font_name, TEXT_NAME)
    final.save(out_png, format="PNG")


def mp3_duration_sec(path: Path) -> float:
    audio = MP3(path)
    if audio.info is None or audio.info.length is None:
        raise RuntimeError(f"Could not read duration: {path}")
    return float(audio.info.length)


def run_ffmpeg(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or "")
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}")


def ffmpeg_intro(intro_png: Path, duration: float, out_mp4: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-r",
        str(FPS),
        "-loop",
        "1",
        "-i",
        str(intro_png),
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=channel_layout=stereo:sample_rate={AUDIO_RATE}",
        "-t",
        str(duration),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(AUDIO_RATE),
        "-ac",
        str(AUDIO_CHANNELS),
        str(out_mp4),
    ]
    run_ffmpeg(cmd)


def ffmpeg_clip(
    slide_png: Path, audio_mp3: Path, out_mp4: Path, duration_sec: float
) -> None:
    """Encode still + trimmed audio. Uniform sample rate avoids concat audio drops."""
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-r",
        str(FPS),
        "-loop",
        "1",
        "-i",
        str(slide_png),
        "-i",
        str(audio_mp3),
        "-t",
        str(duration_sec),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(AUDIO_RATE),
        "-ac",
        str(AUDIO_CHANNELS),
        str(out_mp4),
    ]
    run_ffmpeg(cmd)


def ffmpeg_concat(parts: list[Path], out_mp4: Path) -> None:
    if len(parts) == 1:
        shutil.copyfile(parts[0], out_mp4)
        return
    lst = out_mp4.parent / "_concat_list.txt"
    with lst.open("w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p.as_posix()}'\n")
    # Re-encode so every segment shares identical A/V layout (-c copy was dropping
    # audio in some players when sample rates differed 44.1k vs 48k).
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(lst),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(AUDIO_RATE),
        "-ac",
        str(AUDIO_CHANNELS),
        str(out_mp4),
    ]
    run_ffmpeg(cmd)
    lst.unlink(missing_ok=True)


def strip_display_markdown(line: str) -> str:
    """Remove common lightweight markdown so intro matches on-screen text."""
    s = line.strip()
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", s)
    return s.strip()


def find_quiz_text_path(quiz_dir: Path) -> Path:
    for name in QUIZ_TEXT_FILENAMES:
        path = quiz_dir / name
        if path.is_file():
            return path
    for path in sorted(quiz_dir.iterdir()):
        if (
            path.is_file()
            and path.suffix.lower() == ".md"
            and "text" in path.stem.lower()
            and path.stem.lower() not in {"readme"}
        ):
            return path
    raise FileNotFoundError(
        f"Expected quiz-text.md (or QuixText.md / QuizText.md) in {quiz_dir}"
    )


def write_quiz_text(out_path: Path, source_path: Path, quiz_num: int) -> None:
    text = source_path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"(Carnatic Quiz #)\d+",
        rf"\g<1>{quiz_num}",
        text,
        count=1,
    )
    if count == 0:
        lines = text.splitlines()
        if len(lines) >= 3:
            lines[2] = re.sub(r"#\d+", f"#{quiz_num}", lines[2]) or f"Carnatic Quiz #{quiz_num}"
            updated = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        else:
            updated = text
    out_path.write_text(updated, encoding="utf-8")


def display_name_for_key(key: str, performers: dict[str, str]) -> str:
    if key in performers:
        return performers[key]
    normalized = normalize_stem(key)
    for perf_key, name in performers.items():
        perf_norm = normalize_stem(perf_key)
        if perf_norm == normalized or normalized in perf_norm or perf_norm.startswith(normalized):
            return name
    return key


def build_quiz_metadata(
    quiz_num: int,
    source_audios: list[Path],
    performers: dict[str, str],
) -> str:
    """Answer key: clips 1–3 share the main ragam; clip 4 is the odd ragam."""
    ragam_counts: dict[str, int] = {}
    for audio in source_audios:
        ragam = ragam_from_audio(audio)
        ragam_counts[ragam] = ragam_counts.get(ragam, 0) + 1

    if len(ragam_counts) != 2 or sorted(ragam_counts.values()) != [1, 3]:
        ragam_summary = ", ".join(f"{r}×{c}" for r, c in sorted(ragam_counts.items()))
        raise ValueError(
            f"Expected 3 clips in one ragam and 1 in another, got: {ragam_summary}"
        )

    odd_ragam = min(ragam_counts, key=ragam_counts.get)
    main_ragam = max(ragam_counts, key=ragam_counts.get)
    main_clips = sorted(
        (a for a in source_audios if ragam_from_audio(a) == main_ragam),
        key=lambda p: p.name,
    )
    odd_clip = next(a for a in source_audios if ragam_from_audio(a) == odd_ragam)

    lines = [
        f"# Quiz {quiz_num} — {main_ragam} vs {odd_ragam}",
        "",
        "| Clip | Performer | Ragam | File |",
        "|------|-----------|-------|------|",
    ]
    for slot, audio in enumerate(main_clips, start=1):
        key = performer_key_from_audio(audio)
        name = display_name_for_key(key, performers)
        lines.append(f"| {slot} | {name} | {main_ragam} | {audio.name} |")
    key = performer_key_from_audio(odd_clip)
    name = display_name_for_key(key, performers)
    lines.append(f"| 4 (odd) | {name} | {odd_ragam} | {odd_clip.name} |")
    lines.append("")
    return "\n".join(lines)


def write_output_bundle(
    out_dir: Path,
    quiz_num: int,
    source_audios: list[Path],
    performers: dict[str, str],
    quiz_text_source: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_quiz_text(out_dir / "quiz-text.md", quiz_text_source, quiz_num)
    (out_dir / "quiz-answer.md").write_text(
        build_quiz_metadata(quiz_num, source_audios, performers),
        encoding="utf-8",
    )


def read_quiz_text(quiz_dir: Path) -> list[str]:
    """Load intro copy from quiz-text.md (or legacy names)."""
    return _parse_quiz_text_file(find_quiz_text_path(quiz_dir))


def _parse_quiz_text_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines: list[str] = []
    for ln in text.splitlines():
        raw = ln.strip()
        if not raw:
            continue
        lines.append(strip_display_markdown(raw))
    return lines


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="Build one Carnatic quiz video (intro + 4 clips).")
    p.add_argument(
        "--quiz-dir",
        type=Path,
        default=root / "Quiz39",
        help="Folder containing mp3 files and QuixText.md",
    )
    p.add_argument(
        "--assets-dir",
        type=Path,
        default=root,
        help="Folder with Pics/, performers.json, intro-background.jpg",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output mp4 path (default: completed-videos/Quiz{N}/Quiz{N}_video.mp4)",
    )
    p.add_argument(
        "--completed-videos-dir",
        type=Path,
        default=None,
        help=f"Folder for auto-numbered outputs (default: <assets-dir>/{COMPLETED_VIDEOS_DIRNAME})",
    )
    p.add_argument(
        "--intro-duration",
        type=float,
        default=8.0,
        help="Intro length in seconds",
    )
    p.add_argument(
        "--intro-bg",
        type=Path,
        default=None,
        help="Override intro background image",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for clip order (omit for non-reproducible shuffle)",
    )
    p.add_argument(
        "--clip-max-duration",
        type=float,
        default=CLIP_MAX_DURATION_SEC,
        help="Cap each clip at this many seconds (trim audio; default 30)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    quiz_dir = args.quiz_dir.resolve()
    assets = args.assets_dir.resolve()
    pics_dir = assets / "Pics"
    performers_path = assets / "performers.json"
    intro_bg = (
        args.intro_bg.resolve()
        if args.intro_bg
        else assets / "intro-background.jpg"
    )

    if args.seed is not None:
        random.seed(args.seed)

    if not intro_bg.is_file():
        raise SystemExit(f"Intro background not found: {intro_bg}")
    if not pics_dir.is_dir():
        raise SystemExit(f"Pics folder not found: {pics_dir}")

    performers = load_performers(performers_path)
    quiz_text_source = find_quiz_text_path(quiz_dir)
    lines = read_quiz_text(quiz_dir)
    source_audios = sorted(quiz_dir.glob("*.mp3"))
    audios = list(source_audios)
    if len(audios) != 4:
        raise SystemExit(
            f"Expected exactly 4 mp3 files in {quiz_dir}, found {len(audios)}"
        )

    random.shuffle(audios)

    missing_pics: list[str] = []
    for audio in audios:
        key = performer_key_from_audio(audio)
        try:
            find_performer_image(pics_dir, key)
        except FileNotFoundError:
            missing_pics.append(f"{audio.name} (performer key {key!r})")
    if missing_pics:
        raise SystemExit(
            "Each quiz MP3 needs a matching photo in Pics/. Missing:\n  "
            + "\n  ".join(missing_pics)
        )

    completed_dir = (
        args.completed_videos_dir.resolve()
        if args.completed_videos_dir is not None
        else assets / COMPLETED_VIDEOS_DIRNAME
    )

    out_dir: Path
    quiz_num: int
    out_final = args.output
    if out_final is None:
        out_dir, out_final, quiz_num = next_completed_quiz_output(completed_dir)
    else:
        out_final = out_final.resolve()
        out_dir = out_final.parent
        match = COMPLETED_VIDEO_RE.match(out_final.name)
        dir_match = COMPLETED_QUIZ_DIR_RE.match(out_dir.name)
        if match:
            quiz_num = int(match.group(1))
        elif dir_match:
            quiz_num = int(dir_match.group(1))
        else:
            quiz_num = 0

    out_dir.mkdir(parents=True, exist_ok=True)

    tmpdir = Path(tempfile.mkdtemp(prefix="carnatic_quiz_"))
    try:
        segments: list[Path] = []

        intro_png = tmpdir / "intro.png"
        draw_intro_slide(intro_bg, lines, intro_png)
        intro_mp4 = tmpdir / "seg_intro.mp4"
        ffmpeg_intro(intro_png, args.intro_duration, intro_mp4)
        segments.append(intro_mp4)

        cap = max(0.1, float(args.clip_max_duration))
        for i, audio in enumerate(audios, start=1):
            key = performer_key_from_audio(audio)
            pic_path = find_performer_image(pics_dir, key)
            display_name = display_name_for_key(key, performers)
            slide_png = tmpdir / f"slide_{i}.png"
            draw_clip_slide(pic_path, i, display_name, slide_png)
            seg = tmpdir / f"seg_{i}.mp4"
            dur = min(cap, mp3_duration_sec(audio))
            ffmpeg_clip(slide_png, audio, seg, dur)
            segments.append(seg)

        ffmpeg_concat(segments, out_final)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if quiz_num > 0:
        write_output_bundle(
            out_dir,
            quiz_num,
            source_audios,
            performers,
            quiz_text_source,
        )

    print(f"Wrote {out_final}")
    if quiz_num > 0:
        print(f"Wrote {out_dir / 'quiz-text.md'}")
        print(f"Wrote {out_dir / 'quiz-answer.md'}")


if __name__ == "__main__":
    main()

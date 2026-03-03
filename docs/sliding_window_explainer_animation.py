from __future__ import annotations

import math
from pathlib import Path

import imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1280
HEIGHT = 720
FPS = 20
SCAN_SECONDS = 4.2
SCAN_FRAMES = int(FPS * SCAN_SECONDS)
INTRO_HOLD_SECONDS = 3.0
INTRO_HOLD_FRAMES = int(FPS * INTRO_HOLD_SECONDS)
MATCH_PAUSE_SECONDS = 0.8
MATCH_PAUSE_FRAMES = int(FPS * MATCH_PAUSE_SECONDS)
FINAL_HOLD_SECONDS = 1.0
FINAL_HOLD_FRAMES = int(FPS * FINAL_HOLD_SECONDS)

BACKGROUND = (246, 249, 252)
TEXT = (34, 52, 72)
BAR_BORDER = (44, 69, 94)
BAR_FILL = (252, 253, 255)
TITLE_THEME = (171, 209, 245)
CHAPTER_MELODY = (167, 231, 225)
WINDOW_FILL = (193, 224, 243, 95)
WINDOW_BORDER = (120, 176, 210)
PULSE = (101, 191, 224)
CHAPTER_LINE = (152, 197, 224)

BAR_X0 = 70
BAR_X1 = WIDTH - 70
BAR_Y0 = 340
BAR_Y1 = 420
BAR_W = BAR_X1 - BAR_X0
BAR_H = BAR_Y1 - BAR_Y0

WINDOW_W = 290
WINDOW_H = 150
WINDOW_Y = 288

PATTERN_MARKERS = [
    {"ratio": 0.22, "kind": "title", "label": "Title Theme"},
    {"ratio": 0.56, "kind": "chapter", "label": "Chapter Change"},
    {"ratio": 0.80, "kind": "chapter", "label": "Chapter Change"},
]
DIVIDER_WIDTH = 58
DIVIDER_PADDING = 18
MATCH_TOLERANCE = 0.017

OUTPUT_DIR = Path(__file__).resolve().parent
GIF_PATH = OUTPUT_DIR / "sliding_window_explainer.gif"
MP4_PATH = OUTPUT_DIR / "sliding_window_explainer.mp4"


def load_font(size: int) -> ImageFont.ImageFont:
    for font_name in ("DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()


TITLE_FONT = load_font(34)
LABEL_FONT = load_font(22)
CHAPTER_FONT = load_font(26)


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def divider_rect(center_ratio: float) -> tuple[float, float, float, float]:
    center_x = BAR_X0 + BAR_W * center_ratio
    x0 = center_x - (DIVIDER_WIDTH / 2)
    x1 = center_x + (DIVIDER_WIDTH / 2)
    y0 = BAR_Y0 + DIVIDER_PADDING
    y1 = BAR_Y1 - DIVIDER_PADDING
    return x0, y0, x1, y1


def marker_fill(kind: str) -> tuple[int, int, int]:
    if kind == "title":
        return TITLE_THEME
    return CHAPTER_MELODY


def draw_waveform(draw: ImageDraw.ImageDraw) -> None:
    center_y = (BAR_Y0 + BAR_Y1) / 2
    usable_width = BAR_W - 48
    x_positions = np.linspace(BAR_X0 + 24, BAR_X0 + 24 + usable_width, 84)

    for idx, x_pos in enumerate(x_positions):
        phase = idx / 6.0
        amp = 8 + 18 * (0.5 + 0.5 * math.sin(phase)) * (0.6 + 0.4 * math.sin(phase / 2.7))
        line_color = TEXT if idx % 5 else BAR_BORDER
        draw.line(
            [(x_pos, center_y - amp), (x_pos, center_y + amp)],
            fill=line_color,
            width=3 if idx % 4 else 4,
        )


def window_position(frame_index: int) -> float:
    start_x = BAR_X0 - WINDOW_W * 0.08
    end_x = BAR_X1 - WINDOW_W * 0.35
    clamped_index = min(frame_index, SCAN_FRAMES - 1)
    progress = clamped_index / max(SCAN_FRAMES - 1, 1)
    return start_x + (end_x - start_x) * progress


def active_matches(window_center_ratio: float) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for marker in PATTERN_MARKERS:
        if abs(window_center_ratio - float(marker["ratio"])) <= MATCH_TOLERANCE:
            hits.append(marker)
    return hits


def draw_match_pulse(
    overlay: Image.Image,
    match_ratio: float,
    intensity: float,
    color: tuple[int, int, int],
) -> None:
    pulse_draw = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = divider_rect(match_ratio)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    radius = 24 + int(20 * intensity)
    alpha = int(70 * intensity)
    pulse_draw.ellipse(
        [(cx - radius, cy - radius), (cx + radius, cy + radius)],
        fill=(color[0], color[1], color[2], alpha),
        outline=(color[0], color[1], color[2], min(alpha + 20, 120)),
        width=3,
    )


def draw_checkmark(draw: ImageDraw.ImageDraw, x: float, y: float, scale: float = 1.0) -> None:
    points = [
        (x, y),
        (x + 14 * scale, y + 14 * scale),
        (x + 42 * scale, y - 18 * scale),
    ]
    draw.line(points[:2], fill=TEXT, width=max(2, int(4 * scale)))
    draw.line(points[1:], fill=TEXT, width=max(2, int(4 * scale)))


def draw_chapter_labels(draw: ImageDraw.ImageDraw, visible_count: int) -> None:
    label_y = 485
    chapter_boundaries = [
        marker["ratio"] for marker in PATTERN_MARKERS if marker["kind"] == "chapter"
    ]
    for idx in range(3):
        if idx >= visible_count:
            continue
        start_ratio = 0.0 if idx == 0 else float(chapter_boundaries[idx - 1])
        end_ratio = 1.0 if idx == 2 else float(chapter_boundaries[idx])
        start_x = BAR_X0 + BAR_W * start_ratio
        end_x = BAR_X0 + BAR_W * end_ratio
        label = f"Chapter {idx + 1}"
        label_w, _ = measure_text(draw, label, CHAPTER_FONT)
        label_x = ((start_x + end_x) / 2) - (label_w / 2)
        draw.text((label_x, label_y), label, font=CHAPTER_FONT, fill=TEXT)


def draw_frame(frame_index: int) -> np.ndarray:
    base = Image.new("RGBA", (WIDTH, HEIGHT), BACKGROUND + (255,))
    draw = ImageDraw.Draw(base)

    draw.text((BAR_X0, 225), "Full Story Audio", font=TITLE_FONT, fill=TEXT)
    legend_title_y = 78
    legend_row_y = 112
    status_y = 158

    draw.text((BAR_X0, legend_title_y), "Reference Patterns", font=LABEL_FONT, fill=TEXT)
    draw.rounded_rectangle(
        [(BAR_X0, legend_row_y), (BAR_X0 + 26, legend_row_y + 26)],
        radius=6,
        fill=TITLE_THEME,
    )
    draw.text((BAR_X0 + 40, legend_row_y - 2), "Title Theme", font=LABEL_FONT, fill=TEXT)
    draw.rounded_rectangle(
        [(BAR_X0 + 360, legend_row_y), (BAR_X0 + 386, legend_row_y + 26)],
        radius=6,
        fill=CHAPTER_MELODY,
    )
    draw.text(
        (BAR_X0 + 400, legend_row_y - 2),
        "Chapter Change Melody",
        font=LABEL_FONT,
        fill=TEXT,
    )

    draw.rounded_rectangle(
        [(BAR_X0, BAR_Y0), (BAR_X1, BAR_Y1)],
        radius=18,
        fill=BAR_FILL,
        outline=BAR_BORDER,
        width=4,
    )

    for marker in PATTERN_MARKERS:
        draw.rounded_rectangle(
            divider_rect(float(marker["ratio"])),
            radius=8,
            fill=marker_fill(str(marker["kind"])),
        )

    draw_waveform(draw)

    current_window_x = window_position(frame_index)
    window_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(window_overlay)
    overlay_draw.rounded_rectangle(
        [
            (current_window_x, WINDOW_Y),
            (current_window_x + WINDOW_W, WINDOW_Y + WINDOW_H),
        ],
        radius=14,
        fill=WINDOW_FILL,
        outline=WINDOW_BORDER + (255,),
        width=3,
    )

    label = "Sliding Window"
    label_w, _ = measure_text(overlay_draw, label, TITLE_FONT)
    overlay_draw.text(
        (current_window_x + (WINDOW_W - label_w) / 2, WINDOW_Y + 18),
        label,
        font=TITLE_FONT,
        fill=TEXT,
    )

    base = Image.alpha_composite(base, window_overlay)
    draw = ImageDraw.Draw(base)

    window_center_ratio = ((current_window_x + WINDOW_W / 2) - BAR_X0) / BAR_W
    window_center_ratio = max(0.0, min(1.0, window_center_ratio))
    matches_now = active_matches(window_center_ratio)

    pulse_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    for marker in matches_now:
        match_ratio = float(marker["ratio"])
        distance = abs(window_center_ratio - match_ratio)
        intensity = max(0.0, 1.0 - (distance / MATCH_TOLERANCE))
        draw_match_pulse(
            pulse_overlay,
            match_ratio,
            intensity,
            marker_fill(str(marker["kind"])),
        )
    base = Image.alpha_composite(base, pulse_overlay)
    draw = ImageDraw.Draw(base)

    detected = [
        marker
        for marker in PATTERN_MARKERS
        if window_center_ratio >= float(marker["ratio"]) - MATCH_TOLERANCE
    ]
    chapter_boundaries = [marker for marker in detected if marker["kind"] == "chapter"]
    for marker in chapter_boundaries:
        ratio = float(marker["ratio"])
        line_x = BAR_X0 + BAR_W * ratio
        draw.line([(line_x, BAR_Y1 + 20), (line_x, 560)], fill=CHAPTER_LINE, width=4)

    if matches_now:
        current_match = matches_now[0]
        check_x = BAR_X0 + BAR_W * float(current_match["ratio"]) - 18
        draw_checkmark(draw, check_x, 485, scale=1.0)
        status_text = f"Detected Pattern: {current_match['label']}"
        draw.text((BAR_X0, status_y), status_text, font=LABEL_FONT, fill=TEXT)
    else:
        draw.text(
            (BAR_X0, status_y),
            "Detected Pattern: scanning current section",
            font=LABEL_FONT,
            fill=(96, 116, 136),
        )

    final_state = frame_index >= SCAN_FRAMES
    visible_labels = len(chapter_boundaries) + 1
    if final_state:
        visible_labels = 3
        for marker in PATTERN_MARKERS:
            if marker["kind"] != "chapter":
                continue
            ratio = float(marker["ratio"])
            line_x = BAR_X0 + BAR_W * ratio
            draw.line([(line_x, BAR_Y1 + 20), (line_x, 560)], fill=CHAPTER_LINE, width=4)

    draw_chapter_labels(draw, visible_labels)

    return np.array(base.convert("RGB"))


def build_animation() -> list[np.ndarray]:
    frames: list[np.ndarray] = []
    paused_markers: set[float] = set()

    intro_frame = draw_frame(0)
    for _ in range(INTRO_HOLD_FRAMES):
        frames.append(intro_frame)

    for frame_index in range(SCAN_FRAMES):
        frame = draw_frame(frame_index)
        frames.append(frame)

        current_window_x = window_position(frame_index)
        window_center_ratio = ((current_window_x + WINDOW_W / 2) - BAR_X0) / BAR_W
        window_center_ratio = max(0.0, min(1.0, window_center_ratio))

        for marker in PATTERN_MARKERS:
            marker_ratio = float(marker["ratio"])
            if marker_ratio in paused_markers:
                continue
            if window_center_ratio >= marker_ratio:
                paused_markers.add(marker_ratio)
                for _ in range(MATCH_PAUSE_FRAMES):
                    frames.append(frame)

    if FINAL_HOLD_FRAMES > 0:
        final_frame = draw_frame(SCAN_FRAMES)
        for _ in range(FINAL_HOLD_FRAMES):
            frames.append(final_frame)

    return frames


def main() -> None:
    frames = build_animation()

    imageio.mimsave(GIF_PATH, frames, format="GIF", fps=FPS, loop=0)

    try:
        imageio.mimsave(
            MP4_PATH,
            frames,
            fps=FPS,
            codec="libx264",
            quality=8,
            output_params=["-pix_fmt", "yuv420p", "-movflags", "faststart"],
        )
        print(f"Saved animation GIF: {GIF_PATH}")
        print(f"Saved animation MP4: {MP4_PATH}")
    except Exception:
        print(f"Saved animation GIF: {GIF_PATH}")
        print("MP4 export skipped. Install ffmpeg support to write MP4 output.")


if __name__ == "__main__":
    main()

"""Media files: allowed types, safe storage on disk, and generated placeholder media."""

import json
import math
import struct
import wave
from io import BytesIO
from pathlib import Path

ALLOWED = {
    ".mp4": ("video", "video/mp4"),
    ".m4v": ("video", "video/mp4"),
    ".webm": ("video", "video/webm"),
    ".mov": ("video", "video/quicktime"),
    ".mp3": ("audio", "audio/mpeg"),
    ".m4a": ("audio", "audio/mp4"),
    ".aac": ("audio", "audio/aac"),
    ".wav": ("audio", "audio/wav"),
    ".ogg": ("audio", "audio/ogg"),
    ".png": ("image", "image/png"),
    ".jpg": ("image", "image/jpeg"),
    ".jpeg": ("image", "image/jpeg"),
    ".gif": ("image", "image/gif"),
    ".webp": ("image", "image/webp"),
    ".json": ("lottie", "application/json"),
    ".vtt": ("captions", "text/vtt"),
}
MAX_BYTES = 2 * 1024**3


class MediaError(ValueError):
    pass


def classify(filename: str) -> tuple[str, str, str]:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise MediaError(f"Unsupported file type {ext or '(none)'}. Allowed: {', '.join(sorted(ALLOWED))}")
    kind, mime = ALLOWED[ext]
    return kind, mime, ext


def check_content(kind: str, path: Path) -> None:
    """Light checks on text-based media, so a mislabelled file is caught early."""
    if kind == "lottie":
        try:
            data = json.loads(path.read_text())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MediaError("That .json file isn't valid JSON.") from exc
        if not isinstance(data, dict) or "layers" not in data:
            raise MediaError("That .json file doesn't look like a Lottie animation.")
    elif kind == "captions":
        if not path.read_text(errors="replace").lstrip("﻿").startswith("WEBVTT"):
            raise MediaError("Captions must be a WebVTT (.vtt) file.")


# ---- generated placeholder media (no outside files needed) ----


def placeholder_tone(seconds: float = 3.0, freq: float = 440.0, rate: int = 22050) -> bytes:
    buf = BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = int(seconds * rate)
        fade = int(0.05 * rate)
        samples = []
        for i in range(frames):
            env = min(1.0, i / fade, (frames - i) / fade)
            samples.append(int(0.3 * env * 32767 * math.sin(2 * math.pi * freq * i / rate)))
        w.writeframes(struct.pack(f"<{frames}h", *samples))
    return buf.getvalue()


def _ease(t: int, value: list) -> dict:
    return {"t": t, "s": value, "i": {"x": [0.5], "y": [1]}, "o": {"x": [0.5], "y": [0]}}


def placeholder_lottie() -> bytes:
    """A pulsing circle and a turning ring, as a minimal Lottie animation."""
    transform = {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]},
                 "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}, "sk": {"a": 0, "k": 0}, "sa": {"a": 0, "k": 0}}

    def layer(ind: int, name: str, ks: dict, items: list) -> dict:
        return {"ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1, "ks": ks, "ao": 0,
                "shapes": [{"ty": "gr", "nm": name, "it": [*items, transform]}], "ip": 0, "op": 90, "st": 0, "bm": 0}

    static = {"o": {"a": 0, "k": 100}, "p": {"a": 0, "k": [200, 200, 0]}, "a": {"a": 0, "k": [0, 0, 0]}}
    circle = layer(
        2, "circle",
        {**static, "r": {"a": 0, "k": 0},
         "s": {"a": 1, "k": [_ease(0, [70, 70, 100]), _ease(45, [100, 100, 100]), {"t": 90, "s": [70, 70, 100]}]}},
        [{"ty": "el", "nm": "e", "p": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [180, 180]}},
         {"ty": "fl", "nm": "f", "c": {"a": 0, "k": [0.18, 0.44, 0.87, 1]}, "o": {"a": 0, "k": 100}, "r": 1}],
    )
    ring = layer(
        1, "ring",
        {**static, "s": {"a": 0, "k": [100, 100, 100]},
         "r": {"a": 1, "k": [{"t": 0, "s": [0]}, {"t": 90, "s": [360]}]}},
        [{"ty": "rc", "nm": "r", "p": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [300, 300]}, "r": {"a": 0, "k": 60}},
         {"ty": "st", "nm": "s", "c": {"a": 0, "k": [0.18, 0.44, 0.87, 1]}, "o": {"a": 0, "k": 60},
          "w": {"a": 0, "k": 10}, "lc": 2, "lj": 2}],
    )
    anim = {"v": "5.7.0", "fr": 30, "ip": 0, "op": 90, "w": 400, "h": 400, "nm": "[Placeholder animation]",
            "ddd": 0, "assets": [], "layers": [ring, circle]}
    return json.dumps(anim).encode()

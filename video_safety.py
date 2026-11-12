"""Sample three distinct frames per second and gate playback with Freepik."""
from __future__ import annotations

import json
import math
import random
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Callable

THRESHOLD = 0.8
LEVEL = "low"
_detector = None
_detector_lock = threading.Lock()


class UnsafeVideoError(RuntimeError):
    pass


def get_detector():
    global _detector
    with _detector_lock:
        if _detector is None:
            import torch
            from nsfw_image_detector import NSFWDetector

            # CPU avoids competing with the video model for GPU memory.
            detector = NSFWDetector(
                model_name="Freepik/nsfw_image_detector",
                device="cpu", dtype=torch.float32,
            )
            detector.model.eval()
            _detector = detector
        return _detector


def sample_frames(timestamps: list[float], rng=None) -> list[int]:
    """Use real frame timestamps, including variable FPS and the final partial second."""
    if not timestamps or any(not math.isfinite(t) for t in timestamps):
        raise RuntimeError("Không đọc được thời gian frame của video")
    if any(b < a for a, b in zip(timestamps, timestamps[1:])):
        raise RuntimeError("Thứ tự thời gian frame không hợp lệ")
    rng = rng or random.SystemRandom()
    buckets: dict[int, list[int]] = {}
    start = timestamps[0]
    for index, timestamp in enumerate(timestamps):
        buckets.setdefault(math.floor(timestamp - start), []).append(index)
    return sorted(
        index for frames in buckets.values()
        for index in rng.sample(frames, min(3, len(frames)))
    )


def check_video(path: Path, on_progress: Callable[[int, int], None] | None = None) -> int:
    """Return checked count; reject on any flagged frame or decoding/inference error."""
    from PIL import Image

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames",
         "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    timestamps = [float(frame["best_effort_timestamp_time"])
                  for frame in json.loads(probe.stdout).get("frames", [])]
    indices = sample_frames(timestamps)
    detector = get_detector()
    with tempfile.TemporaryDirectory(prefix="t2v-safety-") as temp:
        expression = "+".join(f"eq(n,{index})" for index in indices)
        decoded = subprocess.run(
            ["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0",
             "-vf", f"select='{expression}'", "-vsync", "0",
             str(Path(temp) / "%06d.png")],
            check=True, capture_output=True, text=True, timeout=180,
        )
        if decoded.stderr.strip():
            raise RuntimeError("Lỗi giải mã video khi kiểm duyệt")
        frames = sorted(Path(temp).glob("*.png"))
        if len(frames) != len(indices):
            raise RuntimeError("Không trích xuất đủ frame để kiểm duyệt")
        for count, frame in enumerate(frames, 1):
            with Image.open(frame) as image:
                flagged = detector.is_nsfw(image.convert("RGB"), threshold_level=LEVEL, threshold=THRESHOLD)
            if flagged:
                raise UnsafeVideoError("Video bị chặn vì phát hiện nội dung NSFW")
            if on_progress:
                on_progress(count, len(frames))
    return len(indices)

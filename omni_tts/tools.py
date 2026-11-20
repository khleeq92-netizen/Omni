"""Locating external programs (ffmpeg) on Linux, Colab, Kaggle and macOS."""

from __future__ import annotations

import shutil
from functools import lru_cache


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str | None:
    """System ffmpeg if installed, else the portable one from imageio-ffmpeg (used on Mac)."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

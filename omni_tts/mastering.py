"""Make raw TTS output sound like a finished voiceover.

Steps: join chunks with natural pauses, remove low rumble, normalise
loudness to a YouTube-friendly level and keep peaks below clipping.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

from .tools import ffmpeg_exe

YOUTUBE_LUFS = -14.0      # YouTube normalises playback to about -14 LUFS
PODCAST_LUFS = -16.0
PEAK_CEILING_DB = -1.0


def silence(seconds: float, sr: int) -> np.ndarray:
    return np.zeros(int(round(seconds * sr)), dtype=np.float32)


def trim_edges(audio: np.ndarray, sr: int, threshold_db: float = -45.0, keep: float = 0.03) -> np.ndarray:
    """Trim leading/trailing near-silence so our own pauses are consistent."""
    if audio.size == 0:
        return audio
    thr = 10 ** (threshold_db / 20) * max(np.max(np.abs(audio)), 1e-9)
    idx = np.where(np.abs(audio) > thr)[0]
    if idx.size == 0:
        return audio
    pad = int(keep * sr)
    return audio[max(idx[0] - pad, 0): min(idx[-1] + pad, audio.size)]


def assemble(paragraphs: list[list[np.ndarray]], sr: int,
             sentence_pause: float = 0.35, paragraph_pause: float = 0.75,
             lead_in: float = 0.3, tail: float = 0.6) -> np.ndarray:
    parts = [silence(lead_in, sr)]
    for pi, chunks in enumerate(paragraphs):
        for ci, chunk in enumerate(chunks):
            parts.append(trim_edges(chunk.astype(np.float32), sr))
            if ci < len(chunks) - 1:
                parts.append(silence(sentence_pause, sr))
        if pi < len(paragraphs) - 1:
            parts.append(silence(paragraph_pause, sr))
    parts.append(silence(tail, sr))
    return np.concatenate(parts)


def change_tempo(audio: np.ndarray, sr: int, speed: float) -> np.ndarray:
    """Speed up / slow down without changing pitch (ffmpeg atempo)."""
    import tempfile
    if not ffmpeg_exe():
        return audio
    speed = min(max(speed, 0.5), 2.0)
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / "in.wav", Path(d) / "out.wav"
        sf.write(src, audio, sr)
        subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(src),
                        "-filter:a", f"atempo={speed:.3f}", str(dst)], check=True)
        out, _ = sf.read(dst, dtype="float32")
    return out


def master(audio: np.ndarray, sr: int, target_lufs: float = YOUTUBE_LUFS) -> np.ndarray:
    audio = audio.astype(np.float64)
    # 1. High-pass at 70 Hz: removes rumble/DC without thinning the voice.
    sos = butter(2, 70, btype="highpass", fs=sr, output="sos")
    audio = sosfilt(sos, audio)
    # 2. Loudness normalisation (ITU-R BS.1770).
    try:
        import pyloudnorm as pyln
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(audio)
        if np.isfinite(loudness):
            audio = audio * 10 ** ((target_lufs - loudness) / 20)
    except ImportError:
        rms = np.sqrt(np.mean(audio ** 2)) or 1.0
        audio = audio * (10 ** ((target_lufs + 3) / 20)) / rms
    # 3. Soft limiter: gently compress only the peaks above the ceiling.
    ceiling = 10 ** (PEAK_CEILING_DB / 20)
    knee = ceiling * 0.8
    mag = np.abs(audio)
    over = mag > knee
    if np.any(over):
        span = ceiling - knee
        mag[over] = knee + span * np.tanh((mag[over] - knee) / span)
        audio = np.sign(audio) * mag
    return audio.astype(np.float32)


def export(audio: np.ndarray, sr: int, out_base: Path, mp3: bool = True) -> dict[str, Path]:
    """Write ``<out_base>.wav`` (48 kHz, 24-bit) and optionally ``.mp3`` (320 kbps)."""
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    wav = out_base.with_suffix(".wav")
    target_sr = 48000  # video editors / YouTube standard
    if sr != target_sr:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr).astype(np.float32)
        np.clip(audio, -0.999, 0.999, out=audio)
    sf.write(wav, audio, target_sr, subtype="PCM_24")
    out["wav"] = wav
    if mp3 and ffmpeg_exe():
        mp3_path = out_base.with_suffix(".mp3")
        subprocess.run(
            [ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(wav),
             "-codec:a", "libmp3lame", "-b:a", "320k", str(mp3_path)],
            check=True,
        )
        out["mp3"] = mp3_path
    return out

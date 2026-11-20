"""Voice styles and background music.

Voice styles are post-processing chains (pitch, EQ, compression, echo) that
work on any voice, cloned or built-in. Background music is either one of the
built-in tracks synthesised here (original, no copyright issues) or a file
the user uploads; it is automatically lowered while the voice speaks.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

# ----------------------------------------------------------------- voice styles
# pitch: semitones (librosa, keeps timing); ffmpeg: audio filter chain.
STYLES: dict[str, dict] = {
    "natural": {"label": "Natural (no effect)", "pitch": 0, "ffmpeg": ""},
    "roabdar": {
        "label": "Roabdar: deep & commanding (रौबदार)", "pitch": -1.5,
        "ffmpeg": ("lowshelf=f=140:g=5,equalizer=f=400:t=q:w=1:g=-2.5,"
                   "equalizer=f=3200:t=q:w=1:g=3,"
                   "acompressor=threshold=0.08:ratio=4:attack=8:release=120:makeup=2,"
                   "aecho=0.8:0.5:35:0.12"),
    },
    "cinematic": {
        "label": "Cinematic trailer: very deep, big hall", "pitch": -3,
        "ffmpeg": ("lowshelf=f=120:g=7,equalizer=f=350:t=q:w=1:g=-3,highshelf=f=6000:g=2,"
                   "acompressor=threshold=0.06:ratio=5:attack=5:release=150:makeup=2.5,"
                   "aecho=0.8:0.7:60|120|180:0.28|0.18|0.1"),
    },
    "studio_warm": {
        "label": "Studio warm: smooth podcast sound", "pitch": 0,
        "ffmpeg": ("lowshelf=f=180:g=2.5,highshelf=f=7000:g=-1.5,"
                   "acompressor=threshold=0.12:ratio=2.5:attack=10:release=150:makeup=1.5"),
    },
    "radio": {
        "label": "Radio announcer: punchy, narrow", "pitch": 0,
        "ffmpeg": ("highpass=f=220,lowpass=f=4200,equalizer=f=1800:t=q:w=1:g=4,"
                   "acompressor=threshold=0.05:ratio=8:attack=3:release=80:makeup=3"),
    },
    "echo": {
        "label": "Dramatic echo: mystery & horror", "pitch": -1,
        "ffmpeg": "lowshelf=f=150:g=3,aecho=0.8:0.6:280|560:0.35|0.18",
    },
    "electro": {
        "label": "Electro voice: robotic / sci-fi", "pitch": 0,
        "ffmpeg": ("chorus=0.6:0.9:40|55:0.4|0.32:0.25|0.4:2|1.3,"
                   "aphaser=in_gain=0.6:out_gain=0.9:delay=2:decay=0.5:speed=0.6,"
                   "equalizer=f=2500:t=q:w=1:g=3"),
    },
}

MUSIC = {
    "none": "No music",
    "electro_pulse": "Electro pulse (energetic, facts & tech)",
    "dark_ambient": "Dark ambient (mystery & horror)",
    "cinematic": "Cinematic drone (documentary & history)",
    "upload": "My own music file (upload)",
}


def _ffmpeg_filter(audio: np.ndarray, sr: int, chain: str) -> np.ndarray:
    if not chain or not shutil.which("ffmpeg"):
        return audio
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / "in.wav", Path(d) / "out.wav"
        sf.write(src, audio, sr, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", chain,
                        "-ar", str(sr), "-ac", "1", str(dst)], check=True)
        out, _ = sf.read(dst, dtype="float32")
    return out


def apply_style(audio: np.ndarray, sr: int, style: str) -> np.ndarray:
    cfg = STYLES.get(style) or STYLES["natural"]
    out = audio.astype(np.float32)
    if cfg["pitch"]:
        import librosa
        out = librosa.effects.pitch_shift(out, sr=sr, n_steps=cfg["pitch"], res_type="soxr_hq")
    out = _ffmpeg_filter(out, sr, cfg["ffmpeg"])
    peak = np.max(np.abs(out)) or 1.0
    return (out / peak * 0.9).astype(np.float32) if peak > 0.9 else out


# ------------------------------------------------------------ built-in music
def _note(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def _env(n: int, sr: int, attack: float, release: float) -> np.ndarray:
    a = min(max(int(attack * sr), 1), max(n // 2, 1))
    r = min(max(int(release * sr), 1), max(n // 2, 1))
    e = np.ones(n, np.float32)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def _lowpass(x: np.ndarray, sr: int, hz: float) -> np.ndarray:
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, hz, btype="lowpass", fs=sr, output="sos"), x).astype(np.float32)


def _pad(chord: list[int], dur: float, sr: int, bright: float = 1200) -> np.ndarray:
    t = np.arange(int(dur * sr)) / sr
    x = np.zeros_like(t, dtype=np.float32)
    for m in chord:
        for det in (-0.08, 0.0, 0.08):  # detuned saws -> warm pad
            f = _note(m + det)
            x += (2 * ((t * f) % 1) - 1).astype(np.float32)
    x = _lowpass(x / (3 * len(chord)), sr, bright)
    return x * _env(len(x), sr, 0.4, 0.6)


def _kick(sr: int) -> np.ndarray:
    t = np.arange(int(0.35 * sr)) / sr
    f = 45 + 90 * np.exp(-t * 30)
    return (np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 9)).astype(np.float32)


def _hat(sr: int, rng) -> np.ndarray:
    n = int(0.05 * sr)
    noise = rng.standard_normal(n).astype(np.float32)
    from scipy.signal import butter, sosfilt
    hp = sosfilt(butter(2, 7000, btype="highpass", fs=sr, output="sos"), noise)
    return (hp * np.exp(-np.arange(n) / sr * 70)).astype(np.float32)


def _place(track: np.ndarray, clip: np.ndarray, start: int, gain: float = 1.0) -> None:
    end = min(start + len(clip), len(track))
    if start < len(track):
        track[start:end] += clip[: end - start] * gain


def make_music(kind: str, seconds: float, sr: int = 48000, seed: int = 7) -> np.ndarray:
    """Synthesise an original background track of ``seconds`` length."""
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    out = np.zeros(n, np.float32)
    if kind == "electro_pulse":
        bpm, beat = 104, 60 / 104
        prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
        bar = 4 * beat
        kick, hat = _kick(sr), _hat(sr, rng)
        for b in range(int(seconds / bar) + 1):
            chord = prog[b % 4]
            _place(out, _pad(chord, bar, sr, 1600), int(b * bar * sr), 0.5)
            root = chord[0] - 24
            t = np.arange(int(beat / 2 * 0.9 * sr)) / sr
            note = (np.sin(2 * np.pi * _note(root) * t) + 0.3 * np.sin(4 * np.pi * _note(root) * t))
            note = (note * np.exp(-t * 6)).astype(np.float32)
            for e in range(8):  # pulsing eighth-note bass
                _place(out, note, int((b * bar + e * beat / 2) * sr), 0.7)
            for q in range(4):
                _place(out, kick, int((b * bar + q * beat) * sr), 0.9)
                _place(out, hat, int((b * bar + q * beat + beat / 2) * sr), 0.25)
        # sidechain-style pump on the pad/bass from the kick
        pump = 1 - 0.45 * np.exp(-((np.arange(n) / sr) % beat) * 12)
        out *= pump.astype(np.float32)
    elif kind == "dark_ambient":
        t = np.arange(n) / sr
        drone = (np.sin(2 * np.pi * _note(33) * t) + 0.6 * np.sin(2 * np.pi * _note(40) * t)
                 + 0.3 * np.sin(2 * np.pi * _note(45.1) * t))
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
        wind = _lowpass(rng.standard_normal(n).astype(np.float32), sr, 400) * 0.6
        wind *= (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t + 1)).astype(np.float32)
        out = (drone * lfo * 0.35).astype(np.float32) + wind * 0.25
        hit = _kick(sr) * 1.2
        for s in np.arange(4.0, seconds, 8.0):
            _place(out, _lowpass(hit, sr, 200), int(s * sr), 0.8)
    elif kind == "cinematic":
        prog = [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 56]]
        bar = 4.0
        for b in range(int(seconds / bar) + 1):
            _place(out, _pad(prog[b % 4], bar + 0.6, sr, 900), int(b * bar * sr), 0.6)
            if b % 2 == 0:
                _place(out, _lowpass(_kick(sr) * 1.5, sr, 160), int(b * bar * sr), 0.9)
    else:
        return out
    fade = min(int(2 * sr), n // 4)
    if fade:
        out[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    peak = np.max(np.abs(out)) or 1.0
    return (out / peak * 0.8).astype(np.float32)


def load_music(path: str, seconds: float, sr: int) -> np.ndarray:
    """Load a user music file, loop it to ``seconds`` and fade the ends."""
    import librosa
    y, _ = librosa.load(path, sr=sr, mono=True)
    n = int(seconds * sr)
    if len(y) == 0:
        return np.zeros(n, np.float32)
    reps = int(np.ceil(n / len(y)))
    y = np.tile(y, reps)[:n].astype(np.float32)
    fade = min(int(2 * sr), n // 4)
    if fade:
        y[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        y[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    return y


def _moving_average(x: np.ndarray, win: int) -> np.ndarray:
    """Centered moving average in O(n) (np.convolve is O(n*win))."""
    win = max(int(win), 1)
    c = np.cumsum(np.concatenate([[0.0], x.astype(np.float64)]))
    out = (c[win:] - c[:-win]) / win
    pad_l = (len(x) - len(out)) // 2
    return np.pad(out, (pad_l, len(x) - len(out) - pad_l), mode="edge").astype(np.float32)


def mix_music(voice: np.ndarray, sr: int, music: np.ndarray, volume_db: float = -18.0,
              duck_db: float = 8.0, tail: float = 1.5) -> np.ndarray:
    """Put music under the voice, lowering it by ``duck_db`` while the voice speaks."""
    n = len(voice) + int(tail * sr)
    music = np.pad(music, (0, max(0, n - len(music))))[:n]
    v = np.pad(voice, (0, n - len(voice)))
    # voice activity envelope (smoothed), 0..1
    win = int(0.05 * sr)
    energy = np.sqrt(_moving_average(v ** 2, win))
    active = (energy > 0.02).astype(np.float32)
    active = _moving_average(active, int(0.3 * sr))
    m_rms = np.sqrt(np.mean(music ** 2)) or 1.0
    v_rms = np.sqrt(np.mean(voice[np.abs(voice) > 0.01] ** 2)) if np.any(np.abs(voice) > 0.01) else 0.1
    base = v_rms / m_rms * 10 ** (volume_db / 20)
    gain = base * 10 ** (-duck_db * active / 20)
    return (v + music * gain).astype(np.float32)


def process(voice: np.ndarray, sr: int, style: str = "natural", music: str = "none",
            music_file: str | None = None, music_volume_db: float = -18.0) -> np.ndarray:
    out = apply_style(voice, sr, style)
    if music and music != "none":
        secs = len(out) / sr + 1.5
        if music == "upload":
            if not music_file:
                return out
            bed = load_music(music_file, secs, sr)
        else:
            bed = make_music(music, secs, sr)
        out = mix_music(out, sr, bed, music_volume_db)
    return out

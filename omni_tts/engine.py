"""Narration engine: script text in, mastered voiceover out (OmniVoice)."""

from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from . import mastering
from .text_clean import prepare_script
from . import pronounce
from .hindi import normalize_hindi, script_check
from .voices import (PRESETS, VOICES_DIR, SavedVoice, load_saved, lock_sample,
                     save_meta)

MODEL_ID = "k2-fsa/OmniVoice"


def pick_device() -> tuple[str, "object"]:
    import torch
    if torch.cuda.is_available():
        return "cuda:0", torch.float16
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps", torch.float16
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return "xpu", torch.float16
    return "cpu", torch.float32


def set_seed(seed: int | None) -> None:
    if seed is None:
        return
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


@dataclass
class NarrationResult:
    files: dict[str, Path]
    duration_s: float
    elapsed_s: float
    chunks: int
    text: str


class Narrator:
    """Both engines are loaded on first use, so using only one costs only its memory."""

    def __init__(self, model_id: str = MODEL_ID, device: str | None = None):
        import torch
        dev, dtype = pick_device()
        if device:
            dev = device
            dtype = torch.float32 if device == "cpu" else torch.float16
        self.device, self._dtype, self._model_id = dev, dtype, model_id
        self._model = None
        self._veena = None
        self.sr = 24000
        self._prompt_cache: dict[str, object] = {}
        self.warnings: list[str] = []

    @property
    def model(self):
        if self._model is None:
            from omnivoice import OmniVoice
            self._model = OmniVoice.from_pretrained(self._model_id, device_map=self.device,
                                                    dtype=self._dtype)
            self.sr = self._model.sampling_rate
        return self._model

    @property
    def veena(self):
        if self._veena is None:
            from .veena import VeenaEngine
            self._veena = VeenaEngine(device=self.device)
        return self._veena

    # ------------------------------------------------------------------ voices
    def _voice_kwargs(self, voice: str) -> tuple[dict, float, str | None]:
        """Resolve a voice name to generate() kwargs, default speed, language."""
        if voice in PRESETS and PRESETS[voice].engine == "veena":
            p = PRESETS[voice]
            return {"veena_speaker": p.instruct}, p.speed, p.language
        saved = load_saved(voice)
        if saved:
            from omnivoice import VoiceClonePrompt
            if saved.prompt_path not in self._prompt_cache:
                self._prompt_cache[saved.prompt_path] = VoiceClonePrompt.load(saved.prompt_path)
            kw = {"voice_clone_prompt": self._prompt_cache[saved.prompt_path]}
            if saved.instruct:
                kw["instruct"] = saved.instruct  # keeps accent/age stable
            return kw, saved.speed, saved.language
        if voice in PRESETS:
            p = PRESETS[voice]
            return {"instruct": p.instruct}, p.speed, p.language
        if voice == "auto":
            return {}, 1.0, None
        # Free-form description, e.g. "female, elderly, low pitch"
        return {"instruct": voice}, 1.0, None

    def audition(self, instruct: str, out_dir: Path, n: int = 3,
                 text: str | None = None, language: str | None = "en",
                 seed_start: int = 1) -> list[tuple[int, Path]]:
        """Generate ``n`` candidate voices for one description (one per seed)."""
        import soundfile as sf
        out_dir.mkdir(parents=True, exist_ok=True)
        text = text or lock_sample(language)
        results = []
        for seed in range(seed_start, seed_start + n):
            set_seed(seed)
            audio = self.model.generate(text=text, instruct=instruct, language=language)[0]
            path = out_dir / f"candidate_seed{seed}.wav"
            sf.write(path, audio, self.sr)
            results.append((seed, path))
        return results

    def lock_voice(self, name: str, instruct: str, seed: int = 1, speed: float = 1.0,
                   language: str | None = "en") -> SavedVoice:
        """Design a voice once and save it so every narration sounds identical."""
        import soundfile as sf
        import torch
        set_seed(seed)
        sample_text = lock_sample(language)
        audio = self.model.generate(text=sample_text, instruct=instruct, language=language)[0]
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        sample = VOICES_DIR / f"{name}_sample.wav"
        sf.write(sample, audio, self.sr)
        prompt = self.model.create_voice_clone_prompt(
            ref_audio=(torch.from_numpy(audio).float().unsqueeze(0), self.sr),
            ref_text=sample_text,
        )
        prompt.save(str(VOICES_DIR / f"{name}.pt"))
        v = SavedVoice(name=name, prompt_path=f"{name}.pt", source=f"design:seed{seed}",
                       instruct=instruct, speed=speed, language=language)
        save_meta(v)
        self._prompt_cache.pop(str(VOICES_DIR / f"{name}.pt"), None)
        return v

    def clone_voice(self, name: str, ref_audio: str, ref_text: str | None,
                    speed: float = 1.0, language: str | None = None) -> SavedVoice:
        """Save a voice cloned from a 3-10 s recording (only with the speaker's consent)."""
        if ref_text is None:
            self.model.load_asr_model()
        prompt = self.model.create_voice_clone_prompt(ref_audio=ref_audio, ref_text=ref_text)
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        prompt.save(str(VOICES_DIR / f"{name}.pt"))
        v = SavedVoice(name=name, prompt_path=f"{name}.pt", source=f"clone:{Path(ref_audio).name}",
                       instruct=None, speed=speed, language=language)
        save_meta(v)
        self._prompt_cache.pop(str(VOICES_DIR / f"{name}.pt"), None)
        return v

    def preview(self, voice: str, language: str | None = None, text: str | None = None,
                out_dir: Path = Path("output/previews")) -> Path:
        """Speak a short sample in ``voice`` (cached, so repeat previews are instant)."""
        import hashlib
        _, _, voice_lang = self._voice_kwargs(voice)
        lang = language or voice_lang
        text = (text or "").strip() or lock_sample(lang)
        key = hashlib.md5(f"{voice}|{lang}|{text}".encode()).hexdigest()[:10]
        base = out_dir / f"{re.sub(r'[^a-zA-Z0-9_-]+', '_', voice)[:40]}_{key}"
        wav = base.with_suffix(".wav")
        if not wav.exists():
            self.narrate(text, base, voice=voice, language=lang, quality="fast", mp3=False)
        return wav

    # --------------------------------------------------------------- narration
    def narrate(self, script: str, out_base: Path, voice: str = "documentary_male",
                speed: float | None = None, language: str | None = None,
                quality: str = "high", seed: int | None = 1234,
                target_lufs: float = mastering.YOUTUBE_LUFS, batch_size: int = 4,
                sentence_pause: float = 0.35, paragraph_pause: float = 0.75,
                mp3: bool = True,
                progress: Callable[[int, int], None] | None = None) -> NarrationResult:
        t0 = time.time()
        self.warnings = []
        kw, default_speed, voice_lang = self._voice_kwargs(voice)
        use_veena = "veena_speaker" in kw
        language = language or voice_lang
        is_hindi = (language or "").lower() in ("hi", "hindi")
        script = pronounce.apply(script)
        if is_hindi:
            # Veena reads Hinglish natively; OmniVoice needs English words in Devanagari.
            if not use_veena and (w := script_check(script)):
                self.warnings.append(w)
            script = normalize_hindi(script, english_to_devanagari=not use_veena)
        # Veena works best on shorter pieces (its context is 2048 tokens).
        paragraphs = prepare_script(script, max_chars=160 if use_veena else 300)
        if not paragraphs:
            raise ValueError("The script has no speakable text after cleaning.")
        speed = speed if speed is not None else default_speed
        num_step = {"draft": 12, "fast": 16, "high": 32}.get(quality, 32)

        flat = [c for p in paragraphs for c in p.chunks]
        audios: list[np.ndarray] = []
        set_seed(seed)
        if use_veena:
            if not is_hindi and _tn_available():
                from omnivoice.utils.text import normalize_text as _norm
                flat = [_norm(c, "en") for c in flat]
            for i, chunk in enumerate(flat):
                audios.append(self.veena.generate(chunk, kw["veena_speaker"],
                                                  seed=None if seed is None else seed + i))
                if progress:
                    progress(i + 1, len(flat))
        for i in range(0, 0 if use_veena else len(flat), batch_size):
            batch = flat[i:i + batch_size]
            n = len(batch)
            call = dict(text=batch, language=[language] * n, speed=[speed] * n,
                        num_step=num_step,
                        normalize_text=_tn_available() and not is_hindi)
            if "voice_clone_prompt" in kw:
                call["voice_clone_prompt"] = [kw["voice_clone_prompt"]] * n
            if "instruct" in kw:
                call["instruct"] = [kw["instruct"]] * n
            audios.extend(self.model.generate(**call))
            if progress:
                progress(min(i + n, len(flat)), len(flat))

        nested, k = [], 0
        for p in paragraphs:
            nested.append(audios[k:k + len(p.chunks)])
            k += len(p.chunks)
        full = mastering.assemble(nested, self.sr, sentence_pause, paragraph_pause)
        if use_veena and abs(speed - 1.0) > 0.01:
            full = mastering.change_tempo(full, self.sr, speed)  # Veena has no speed control
        full = mastering.master(full, self.sr, target_lufs)
        files = mastering.export(full, self.sr, out_base, mp3=mp3)
        clean_text = "\n\n".join(" ".join(p.chunks) for p in paragraphs)
        out_base.with_suffix(".txt").write_text(clean_text, encoding="utf-8")
        files["txt"] = out_base.with_suffix(".txt")
        return NarrationResult(files, len(full) / self.sr, time.time() - t0, len(flat), clean_text)


def _tn_available() -> bool:
    # English/Chinese normalisation needs WeTextProcessing (`pip install omnivoice[tn]`);
    # without it OmniVoice raises, so only turn it on when it is installed.
    try:
        import tn  # noqa: F401
        return True
    except Exception:
        return False

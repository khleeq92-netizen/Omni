"""Voice presets and saved ("locked") voices.

A *preset* is a voice-design description (gender, age, pitch, accent...).
Voice design gives a slightly different voice each time, so for a channel
you "lock" a preset: generate one sample, then save it as a voice-clone
prompt in ``voices/<name>.pt``. Every later narration with that name uses
the exact same voice.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

VOICES_DIR = Path(__file__).resolve().parent.parent / "voices"

# Sample text used when locking a voice. It is calm, neutral narration so the
# saved voice is suited to long-form voiceover.
LOCK_SAMPLE_TEXT = (
    "Welcome back. Today we are going to explore a story that very few people "
    "know about, and by the end of this video, you will see the world a little differently."
)


@dataclass
class Preset:
    name: str
    instruct: str
    description: str
    speed: float = 1.0


PRESETS: dict[str, Preset] = {
    p.name: p
    for p in [
        Preset("documentary_male", "male, middle-aged, low pitch, british accent",
               "Deep, calm British narrator for documentaries and history.", 0.95),
        Preset("documentary_female", "female, middle-aged, moderate pitch, british accent",
               "Warm, authoritative British narrator.", 0.95),
        Preset("explainer_male", "male, young adult, moderate pitch, american accent",
               "Clear, friendly American voice for facts and explainers.", 1.0),
        Preset("explainer_female", "female, young adult, moderate pitch, american accent",
               "Bright, clear American voice for facts and tutorials.", 1.0),
        Preset("storyteller_elder", "male, elderly, low pitch",
               "Older, slow storyteller for folk tales and history.", 0.9),
        Preset("deep_trailer", "male, middle-aged, very low pitch, american accent",
               "Very deep, dramatic voice for motivation and trailers.", 0.92),
        Preset("mystery_whisper", "male, young adult, low pitch, whisper",
               "Whispered voice for horror and mystery.", 0.9),
        Preset("indian_english_male", "male, young adult, moderate pitch, indian accent",
               "Indian-English narrator.", 1.0),
        Preset("indian_english_female", "female, young adult, moderate pitch, indian accent",
               "Indian-English narrator.", 1.0),
    ]
}


@dataclass
class SavedVoice:
    name: str
    prompt_path: str
    source: str          # "preset:<name>" or "clone:<file>"
    instruct: str | None
    speed: float = 1.0
    language: str | None = None


def _meta_path(name: str) -> Path:
    return VOICES_DIR / f"{name}.json"


def save_meta(v: SavedVoice) -> None:
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    _meta_path(v.name).write_text(json.dumps(asdict(v), indent=2), encoding="utf-8")


def load_saved(name: str) -> SavedVoice | None:
    p = _meta_path(name)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    v = SavedVoice(**data)
    prompt = Path(v.prompt_path)
    if not prompt.is_absolute():
        v.prompt_path = str(VOICES_DIR / prompt)
    return v


def list_saved() -> list[SavedVoice]:
    if not VOICES_DIR.exists():
        return []
    out = []
    for p in sorted(VOICES_DIR.glob("*.json")):
        v = load_saved(p.stem)
        if v and Path(v.prompt_path).exists():
            out.append(v)
    return out


def all_voice_names() -> list[str]:
    """Saved (locked) voices first, then presets not yet locked."""
    saved = [v.name for v in list_saved()]
    return saved + [n for n in PRESETS if n not in saved]

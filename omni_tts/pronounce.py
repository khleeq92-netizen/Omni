"""Your own pronunciation fixes: 'word = how to say it'.

Stored in voices/pronunciations.txt (kept in Google Drive together with your
saved voices), applied to every script before narration, in any language.

Example file:
    # Hindi
    शाहजहाँ = शाह जहाँ
    Kulfi = कुल्फ़ी
    # English
    Omni = Om-nee
"""

from __future__ import annotations

import re

from .voices import VOICES_DIR

PRON_FILE = VOICES_DIR / "pronunciations.txt"

EXAMPLE = """# Your pronunciation fixes: one per line, written as   word = how to say it
# Lines starting with # are ignored. Matching ignores upper/lower case.
#
# Examples:
# शाहजहाँ = शाह जहाँ
# YouTube = यूट्यूब
# GIF = जिफ़
"""


def load_text() -> str:
    try:
        return PRON_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return EXAMPLE


def save_text(text: str) -> int:
    PRON_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRON_FILE.write_text(text.strip() + "\n", encoding="utf-8")
    return len(parse(text))


def parse(text: str) -> dict[str, str]:
    rules: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        word, say = (part.strip() for part in line.split("=", 1))
        if word and say:
            rules[word] = say
    return rules


def apply(text: str, rules: dict[str, str] | None = None) -> str:
    rules = parse(load_text()) if rules is None else rules
    # Longest first so "New York" wins over "New".
    for word in sorted(rules, key=len, reverse=True):
        # Word boundaries that also work for Devanagari (\b does not, because
        # vowel signs are not "word" characters).
        pattern = rf"(?<![\wऀ-ॿ]){re.escape(word)}(?![\wऀ-ॿ])"
        text = re.sub(pattern, rules[word], text, flags=re.IGNORECASE)
    return text

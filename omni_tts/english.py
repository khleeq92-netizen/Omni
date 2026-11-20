"""English number reading without WeTextProcessing (which has no Apple Silicon wheel).

Uses num2words:  1859 -> eighteen fifty-nine,  3,000 -> three thousand,
2.5 -> two point five,  25% -> twenty-five percent,  $100 -> one hundred dollars,
21st -> twenty-first.
"""

from __future__ import annotations

import re

_PROTECT_RE = re.compile(r"\[[^\]]*\]")


def normalize_english(text: str) -> str:
    try:
        from num2words import num2words
    except ImportError:
        return text
    saved: list[str] = []
    text = _PROTECT_RE.sub(lambda m: saved.append(m.group(0)) or chr(0xE000 + len(saved) - 1), text)

    def ordinal(m: re.Match) -> str:
        return num2words(int(m.group(1)), to="ordinal")

    def number(m: re.Match) -> str:
        cur, raw, frac, pct = m.group(1), m.group(2), m.group(3), m.group(4)
        digits = raw.replace(",", "")
        if len(digits) > 15:
            out = " ".join(num2words(int(d)) for d in digits)
        elif ("," not in raw and len(digits) == 4 and not (cur or frac or pct)
              and 1100 <= int(digits) <= 2099):
            out = num2words(int(digits), to="year")
        else:
            out = num2words(int(digits))
        if frac:
            out += " point " + " ".join(num2words(int(d)) for d in frac)
        if pct:
            out += " percent"
        if cur:
            unit = {"$": "dollars", "£": "pounds", "€": "euros", "₹": "rupees"}[cur]
            out += " " + (unit[:-1] if out == "one" else unit)
        return out

    text = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b", ordinal, text)
    text = re.sub(r"([$£€₹])?\b(\d[\d,]*\d|\d)(?:\.(\d+))?(?:\s?(%))?", number, text)
    text = re.sub("[-]", lambda m: saved[ord(m.group(0)) - 0xE000], text)
    return text

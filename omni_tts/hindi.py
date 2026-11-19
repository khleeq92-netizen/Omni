"""Hindi text helpers: numbers to spoken Hindi words, script checks.

OmniVoice's built-in normaliser has no Hindi support (num2words lacks
Hindi), so "1947" would be read badly. This converts numbers the way a
Hindi narrator says them:

    1947      -> उन्नीस सौ सैंतालीस        (years 1100-1999 read in hundreds)
    2024      -> दो हज़ार चौबीस
    1,50,000  -> एक लाख पचास हज़ार          (Indian grouping: हज़ार, लाख, करोड़)
    3.5       -> तीन दशमलव पाँच
    25%       -> पच्चीस प्रतिशत
    ₹500      -> पाँच सौ रुपये
"""

from __future__ import annotations

import re

_UNITS = (
    "शून्य एक दो तीन चार पाँच छह सात आठ नौ "
    "दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस "
    "बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस "
    "तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस "
    "चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास "
    "पचास इक्यावन बावन तिरेपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ "
    "साठ इकसठ बासठ तिरेसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर "
    "सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उन्यासी "
    "अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी "
    "नब्बे इक्यानबे बानबे तिरानबे चौरानबे पंचानबे छियानबे सत्तानबे अट्ठानबे निन्यानबे"
).split()
assert len(_UNITS) == 100

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def _below_thousand(n: int) -> list[str]:
    words = []
    if n >= 100:
        words += [_UNITS[n // 100], "सौ"]
        n %= 100
    if n:
        words.append(_UNITS[n])
    return words


def number_to_hindi(n: int, year_style: bool = False) -> str:
    if n == 0:
        return _UNITS[0]
    if n < 0:
        return "माइनस " + number_to_hindi(-n)
    if year_style and 1100 <= n <= 1999 and n % 1000 >= 100:
        hi, lo = divmod(n, 100)
        return " ".join([_UNITS[hi], "सौ"] + ([_UNITS[lo]] if lo else []))
    words: list[str] = []
    for value, name in ((10**7, "करोड़"), (10**5, "लाख"), (1000, "हज़ार")):
        if n >= value:
            q, n = divmod(n, value)
            words += (number_to_hindi(q).split() if q >= 100 else [_UNITS[q]]) + [name]
    words += _below_thousand(n)
    return " ".join(words)


def _digits(s: str) -> str:
    return " ".join(_UNITS[int(d)] for d in s)


def normalize_hindi(text: str) -> str:
    text = text.translate(_DEVANAGARI_DIGITS)

    def repl(m: re.Match) -> str:
        cur, raw, frac, pct = m.group(1), m.group(2), m.group(3), m.group(4)
        digits = raw.replace(",", "")
        if len(digits) > 15:
            out = _digits(digits)
        else:
            plain = "," not in raw and len(digits) == 4 and not cur and not frac and not pct
            out = number_to_hindi(int(digits), year_style=plain)
        if frac:
            out += " दशमलव " + _digits(frac)
        if pct:
            out += " प्रतिशत"
        if cur:
            out += " रुपये"
        return out

    text = re.sub(r"(₹|रु\.?\s?|Rs\.?\s?)?(\d[\d,]*\d|\d)(?:\.(\d+))?(?:\s?(%))?", repl, text)
    return re.sub(r"\s{2,}", " ", text)


def script_check(text: str) -> str | None:
    """Warn when Hindi was requested but the script is written in English letters."""
    deva = len(_DEVANAGARI_RE.findall(text))
    latin = len(_LATIN_RE.findall(text))
    if latin > 20 and latin > deva * 2:
        return ("The script looks like Roman Hindi (Hinglish). For natural Hindi pronunciation, "
                "write it in Devanagari, e.g. ask ChatGPT: 'Write this script in Hindi (Devanagari script)'.")
    return None

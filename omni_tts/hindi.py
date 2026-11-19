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


# --------------------------------------------------------------- English words
# Letter names for spelling out abbreviations (AI -> एआई, GDP -> जीडीपी).
_LETTERS = {
    "A": "ए", "B": "बी", "C": "सी", "D": "डी", "E": "ई", "F": "एफ़", "G": "जी", "H": "एच",
    "I": "आई", "J": "जे", "K": "के", "L": "एल", "M": "एम", "N": "एन", "O": "ओ", "P": "पी",
    "Q": "क्यू", "R": "आर", "S": "एस", "T": "टी", "U": "यू", "V": "वी", "W": "डब्ल्यू",
    "X": "एक्स", "Y": "वाई", "Z": "ज़ेड",
}

# English words that commonly appear inside Hindi YouTube scripts, written the
# way Hindi speakers say them. Abbreviations read as a word (NASA) live here too.
ENGLISH_TO_HINDI = {
    # platforms, brands, tech
    "youtube": "यूट्यूब", "google": "गूगल", "facebook": "फ़ेसबुक", "instagram": "इंस्टाग्राम",
    "whatsapp": "व्हाट्सऐप", "twitter": "ट्विटर", "chatgpt": "चैटजीपीटी", "iphone": "आईफ़ोन",
    "android": "एंड्रॉइड", "apple": "ऐपल", "microsoft": "माइक्रोसॉफ़्ट", "amazon": "अमेज़न",
    "tesla": "टेस्ला", "netflix": "नेटफ़्लिक्स", "internet": "इंटरनेट", "online": "ऑनलाइन",
    "offline": "ऑफ़लाइन", "mobile": "मोबाइल", "phone": "फ़ोन", "smartphone": "स्मार्टफ़ोन",
    "computer": "कंप्यूटर", "laptop": "लैपटॉप", "app": "ऐप", "website": "वेबसाइट",
    "software": "सॉफ़्टवेयर", "technology": "टेक्नोलॉजी", "robot": "रोबोट", "data": "डेटा",
    "video": "वीडियो", "videos": "वीडियोज़", "channel": "चैनल", "subscribe": "सब्सक्राइब",
    "like": "लाइक", "share": "शेयर", "comment": "कमेंट", "comments": "कमेंट्स",
    "bell": "बेल", "icon": "आइकन", "link": "लिंक", "description": "डिस्क्रिप्शन",
    "shorts": "शॉर्ट्स", "viral": "वायरल", "trend": "ट्रेंड", "content": "कॉन्टेंट",
    "creator": "क्रिएटर", "views": "व्यूज़", "followers": "फ़ॉलोअर्स",
    # science, space, organisations read as words
    "nasa": "नासा", "isro": "इसरो", "unesco": "यूनेस्को", "nato": "नाटो", "covid": "कोविड",
    "space": "स्पेस", "planet": "प्लैनेट", "mission": "मिशन", "rocket": "रॉकेट",
    "satellite": "सैटेलाइट", "science": "साइंस", "scientist": "साइंटिस्ट", "scientists": "साइंटिस्ट्स",
    "research": "रिसर्च", "virus": "वायरस", "doctor": "डॉक्टर", "hospital": "हॉस्पिटल",
    # everyday words
    "fact": "फ़ैक्ट", "facts": "फ़ैक्ट्स", "story": "स्टोरी", "mystery": "मिस्ट्री",
    "history": "हिस्ट्री", "secret": "सीक्रेट", "amazing": "अमेज़िंग", "interesting": "इंटरेस्टिंग",
    "world": "वर्ल्ड", "record": "रिकॉर्ड", "top": "टॉप", "number": "नंबर", "list": "लिस्ट",
    "team": "टीम", "company": "कंपनी", "business": "बिज़नेस", "market": "मार्केट",
    "money": "मनी", "bank": "बैंक", "plan": "प्लान", "project": "प्रोजेक्ट", "school": "स्कूल",
    "college": "कॉलेज", "office": "ऑफ़िस", "job": "जॉब", "success": "सक्सेस",
    "motivation": "मोटिवेशन", "life": "लाइफ़", "time": "टाइम", "problem": "प्रॉब्लम",
    "solution": "सॉल्यूशन", "idea": "आइडिया", "power": "पावर", "energy": "एनर्जी",
    "game": "गेम", "match": "मैच", "cricket": "क्रिकेट", "film": "फ़िल्म", "movie": "मूवी",
    "music": "म्यूज़िक", "news": "न्यूज़", "update": "अपडेट", "level": "लेवल", "test": "टेस्ट",
    "ok": "ओके", "okay": "ओके", "hello": "हैलो", "hi": "हाय", "bye": "बाय", "sorry": "सॉरी",
    "thank you": "थैंक यू", "thanks": "थैंक्स", "please": "प्लीज़", "friends": "फ़्रेंड्स",
    "guys": "गाइज़", "welcome": "वेलकम", "back": "बैक",
    # countries / places often left in English
    "india": "इंडिया", "america": "अमेरिका", "usa": "यूएसए", "uk": "यूके", "china": "चाइना",
    "japan": "जापान", "russia": "रशिया", "europe": "यूरोप", "london": "लंदन",
    "new york": "न्यूयॉर्क", "dubai": "दुबई",
}

_UNITS_MAP = [
    (r"°\s?C\b", " डिग्री सेल्सियस"), (r"°\s?F\b", " डिग्री फ़ारेनहाइट"), (r"°", " डिग्री"),
    (r"\bkm/h\b", " किलोमीटर प्रति घंटा"), (r"\bkmph\b", " किलोमीटर प्रति घंटा"),
    (r"\bkm\b", " किलोमीटर"), (r"\bkg\b", " किलोग्राम"), (r"\bcm\b", " सेंटीमीटर"),
    (r"\bmm\b", " मिलीमीटर"), (r"\bml\b", " मिलीलीटर"), (r"\bgm\b", " ग्राम"),
    (r"\bmph\b", " मील प्रति घंटा"), (r"\bGB\b", " जीबी"), (r"\bMB\b", " एमबी"),
    (r"&", " और "), (r"\bvs\.?\b", " बनाम "), (r"\betc\.?", " वगैरह"),
    (r"\bDr\.\s?", "डॉक्टर "), (r"\bMr\.\s?", "मिस्टर "), (r"\bMrs\.\s?", "मिसेज़ "),
]

_PROTECT_RE = re.compile(r"\[[^\]]*\]")  # OmniVoice tags like [laughter]


def _spell(acronym: str) -> str:
    return "".join(_LETTERS.get(c, c) for c in acronym.upper())


def transliterate_english(text: str) -> str:
    """Convert English words / abbreviations inside Hindi text to Devanagari."""
    multi = sorted((k for k in ENGLISH_TO_HINDI if " " in k), key=len, reverse=True)
    for k in multi:
        text = re.sub(rf"(?<![A-Za-z]){re.escape(k)}(?![A-Za-z])", ENGLISH_TO_HINDI[k], text,
                      flags=re.IGNORECASE)

    def word(m: re.Match) -> str:
        w = m.group(0)
        key = w.lower().replace("'", "")
        if key in ENGLISH_TO_HINDI:
            return ENGLISH_TO_HINDI[key]
        if re.fullmatch(r"[A-Z](\.[A-Z])+\.?", w):  # U.S.A.
            return _spell(w.replace(".", ""))
        if w.isalpha() and w.isupper() and 2 <= len(w) <= 6:   # GDP, CEO, IPL
            return _spell(w)
        return w  # unknown words stay as they are
    return re.sub(r"[A-Za-z](?:[A-Za-z.']*[A-Za-z])?", word, text)


def _time(m: re.Match) -> str:
    h, mnt = int(m.group(1)), int(m.group(2))
    if mnt == 0:
        return f"{number_to_hindi(h)} बजे"
    if mnt == 30 and h:
        return f"साढ़े {number_to_hindi(h)} बजे" if h > 2 else ("डेढ़ बजे" if h == 1 else "ढाई बजे")
    return f"{number_to_hindi(h)} बजकर {number_to_hindi(mnt)} मिनट"


def normalize_hindi(text: str, english_to_devanagari: bool = True) -> str:
    """Prepare Hindi text for speech.

    ``english_to_devanagari``: convert English words to Devanagari. Needed for
    OmniVoice; Veena reads mixed Hindi-English (Hinglish) natively, so it is
    switched off for Veena.
    """
    text = text.translate(_DEVANAGARI_DIGITS)
    # Keep [tags] untouched.
    saved: list[str] = []
    text = _PROTECT_RE.sub(lambda m: saved.append(m.group(0)) or chr(0xE000 + len(saved) - 1), text)

    text = re.sub(r"\b(\d{1,2}):(\d{2})\b(?:\s*बजे)?", _time, text)
    text = re.sub(r"\$\s?(\d[\d,]*(?:\.\d+)?)", r"\1 डॉलर", text)
    for pat, rep in _UNITS_MAP:
        text = re.sub(pat, rep, text)
    if english_to_devanagari:
        text = transliterate_english(text)

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
    text = re.sub("[\ue000-\ue0ff]", lambda m: saved[ord(m.group(0)) - 0xE000], text)
    text = re.sub(r" +([,।.!?])", r"\1", text)
    return re.sub(r"[ \t]{2,}", " ", text)  # keep line breaks (paragraphs)


def script_check(text: str) -> str | None:
    """Warn when Hindi was requested but the script is written in English letters."""
    deva = len(_DEVANAGARI_RE.findall(text))
    latin = len(_LATIN_RE.findall(text))
    if latin > 20 and latin > deva * 2:
        return ("The script looks like Roman Hindi (Hinglish). For natural Hindi pronunciation, "
                "write it in Devanagari, e.g. ask ChatGPT: 'Write this script in Hindi (Devanagari script)'.")
    return None

"""Turn a ChatGPT-style script into clean, speakable text.

ChatGPT output usually contains Markdown (headings, **bold**, bullet points,
links), emojis and stage directions that a TTS model would either read out
loud or stumble over. This module strips all of that and splits the script
into paragraphs and sentence-sized chunks the model handles reliably.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Non-verbal tags OmniVoice understands; everything else in [brackets] is
# treated as a stage direction and removed.
OMNIVOICE_TAGS = {
    "laughter", "sigh", "confirmation-en", "question-en", "question-ah",
    "question-oh", "question-ei", "question-yi", "surprise-ah", "surprise-oh",
    "surprise-wa", "surprise-yo", "dissatisfaction-hnn",
}

_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # pictographs, emoticons, symbols, flags
    "\U00002600-\U000027BF"  # misc symbols & dingbats
    "\U0000FE0F\U0000200D"   # variation selector, zero-width joiner
    "\U00002B00-\U00002BFF"
    "]+"
)

# Lines that are labels, not narration ("Title:", "[Intro music]", "Scene 2").
_LABEL_LINE_RE = re.compile(
    r"^\s*(title|video title|thumbnail|scene\s*\d*|section\s*\d*|part\s*\d*|"
    r"intro|outro|hook|cta|call to action|narrator|voiceover|voice over|vo)\s*[:\-–]?\s*$",
    re.IGNORECASE,
)
_SPEAKER_PREFIX_RE = re.compile(
    r"^\s*(narrator|voiceover|voice over|vo|host)\s*[:\-–]\s*", re.IGNORECASE
)
# Chatbot chatter around the script ("Sure! Here's your script:", "Let me know...").
_PREAMBLE_RE = re.compile(
    r"^(sure|certainly|absolutely|of course|okay|ok|great|here)\b.{0,120}"
    r"\b(script|voice ?over|narration|draft|version)\b.{0,60}[:!.]$",
    re.IGNORECASE,
)
_SIGNOFF_RE = re.compile(
    r"^(let me know|i hope|hope this|feel free|would you like|want me to|if you('d| would) like)\b",
    re.IGNORECASE,
)
_HEADING_LABEL_RE = re.compile(
    r"^(part|scene|section|chapter|segment|step)\s*\d+\s*[:\-–.]\s*", re.IGNORECASE
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…।؟])\s+")


@dataclass
class Paragraph:
    chunks: list[str] = field(default_factory=list)


def _clean_line(line: str) -> str:
    line = _SPEAKER_PREFIX_RE.sub("", line)
    # Markdown links/images: [text](url) -> text
    line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\((?:[^)]*)\)", r"\1", line)
    # Bare URLs
    line = re.sub(r"https?://\S+", "", line)
    # Stage directions in [] or () except OmniVoice tags / CMU phonemes.
    def _bracket(m: re.Match) -> str:
        inner = m.group(1).strip()
        if inner.lower() in OMNIVOICE_TAGS:
            return f"[{inner.lower()}]"
        if re.fullmatch(r"[A-Z]{1,3}[0-2]?(?:\s+[A-Z]{1,3}[0-2]?)*", inner):
            return m.group(0)  # CMU pronunciation like [B EY1 S]
        return ""
    line = re.sub(r"\[([^\]]*)\]", _bracket, line)
    line = re.sub(
        r"\((?:[^)]*\b(?:music|sfx|sound|pause|beat|cut to|b-roll|visual|on screen|scene)\b[^)]*)\)",
        "", line, flags=re.IGNORECASE,
    )
    # Headings, quotes, bullets, numbered lists
    line = re.sub(r"^\s*#{1,6}\s*", "", line)
    line = re.sub(r"^\s*>\s*", "", line)
    line = re.sub(r"^\s*[-*•●▪◦]\s+", "", line)
    line = re.sub(r"^\s*\d+[.)]\s+", "", line)
    # Bold / italic / inline code / strikethrough
    line = re.sub(r"(\*\*|__)(.+?)\1", r"\2", line)
    line = re.sub(r"(?<![\w*])[*_](.+?)[*_](?![\w*])", r"\1", line)
    line = re.sub(r"`([^`]*)`", r"\1", line)
    line = re.sub(r"~~(.+?)~~", r"\1", line)
    line = line.replace("*", "")
    line = _EMOJI_RE.sub("", line)
    # Hashtags (social-post leftovers) are not narrated.
    line = re.sub(r"(?<!\w)#\w+", "", line)
    # Typographic cleanup
    line = line.replace("—", ", ").replace("–", ", ")
    line = re.sub(r"\s*\.{3,}", "…", line)
    line = re.sub(r"\s+([,.!?;:…])", r"\1", line)
    line = re.sub(r",\s*,+", ",", line)
    line = re.sub(r"\s{2,}", " ", line)
    return line.strip(" ,")


def _stop(text: str) -> str:
    """Sentence-ending mark in the text's own script (। for Devanagari)."""
    return "।" if re.search(r"[\u0900-\u097F]", text) else "."


def _ends_sentence(text: str) -> bool:
    return bool(re.search(r"[.!?…।؟:;\]]$", text.rstrip("\"'”’)")))


def clean_script(raw: str) -> list[str]:
    """Return a list of clean paragraphs (each a single string)."""
    raw = raw.replace("\r\n", "\n")
    raw = re.sub(r"```.*?```", "", raw, flags=re.DOTALL)  # code blocks
    paragraphs: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            paragraphs.append(" ".join(current))
            current.clear()

    for line in raw.split("\n"):
        if not line.strip() or re.fullmatch(r"\s*([-*_=]\s*){3,}", line):
            flush()
            continue
        if _LABEL_LINE_RE.match(line.strip(" *#:")):
            flush()
            continue
        is_heading = bool(re.match(r"^\s*#{1,6}\s", line)) or bool(
            re.fullmatch(r"\s*\*\*[^*]+\*\*\s*:?\s*", line)
        )
        is_bullet = bool(re.match(r"^\s*([-*•●▪◦]|\d+[.)])\s+", line))
        cleaned = _clean_line(line)
        if not cleaned:
            continue
        if is_heading:
            flush()
            cleaned = _HEADING_LABEL_RE.sub("", cleaned) or cleaned
            if not _ends_sentence(cleaned):
                cleaned += _stop(cleaned)
            paragraphs.append(cleaned)
            continue
        if is_bullet and not _ends_sentence(cleaned):
            cleaned += _stop(cleaned)
        current.append(cleaned)
    flush()
    paragraphs = [p for p in paragraphs if re.search(r"\w", p)]
    if paragraphs and _PREAMBLE_RE.match(paragraphs[0]):
        paragraphs = paragraphs[1:]
    while paragraphs and _SIGNOFF_RE.match(paragraphs[-1]):
        paragraphs.pop()
    return paragraphs


def split_sentences(paragraph: str, max_chars: int = 300) -> list[str]:
    """Group sentences into chunks of at most ``max_chars`` characters.

    Shorter chunks keep each generation stable (OmniVoice is best at
    ~5-20 second segments) and let us place natural pauses between them.
    """
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(paragraph) if s.strip()]
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        # Split a single over-long sentence on commas.
        while len(s) > max_chars:
            cut = s.rfind(",", 0, max_chars)
            if cut < max_chars // 3:
                cut = s.rfind(" ", 0, max_chars)
            if cut <= 0:
                cut = max_chars
            head, s = s[: cut + 1].strip(), s[cut + 1 :].strip()
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.append(head)
        if not s:
            continue
        if buf and len(buf) + 1 + len(s) > max_chars:
            chunks.append(buf)
            buf = s
        else:
            buf = f"{buf} {s}".strip()
    if buf:
        chunks.append(buf)
    return chunks


def prepare_script(raw: str, max_chars: int = 300) -> list[Paragraph]:
    return [Paragraph(split_sentences(p, max_chars)) for p in clean_script(raw)]

from omni_tts.text_clean import clean_script, split_sentences, prepare_script

CHATGPT = """Sure! Here's your script:

# The Mystery of the Lost City 🏛️

**Hook:**
Did you know that an entire city vanished *overnight*? [Dramatic music]

## Part 1: The Discovery
- It was found in **1911**.
- Explorers called it "the city in the clouds"
Narrator: Nobody expected what came next... (pause)

[laughter] Visit https://example.com for more! #history
---
He played the [B EY1 S] guitar.
"""

def test_clean_markdown():
    paras = clean_script(CHATGPT)
    text = " ".join(paras)
    for bad in ["#", "*", "🏛", "Dramatic music", "https", "Narrator", "Hook", "(pause)"]:
        assert bad not in text, bad
    assert "The Mystery of the Lost City." in paras
    assert "[laughter]" in text and "[B EY1 S]" in text
    assert "It was found in 1911. Explorers called it" in text
    assert "Did you know that an entire city vanished overnight?" in text

def test_split_respects_limit():
    para = " ".join(["This is a fairly ordinary sentence number %d." % i for i in range(40)])
    chunks = split_sentences(para, max_chars=200)
    assert all(len(c) <= 200 for c in chunks)
    assert " ".join(chunks) == para

def test_long_sentence_split():
    s = "word, " * 200 + "end."
    assert all(len(c) <= 300 for c in split_sentences(s))

def test_prepare():
    ps = prepare_script(CHATGPT)
    assert ps and all(p.chunks for p in ps)

def test_preamble_signoff_labels():
    paras = clean_script(CHATGPT + "\nLet me know if you want a shorter version!")
    assert not paras[0].startswith("Sure")
    assert "Let me know" not in " ".join(paras)
    assert "The Discovery." in paras
    assert "history" not in " ".join(paras)


def test_hindi_numbers():
    from omni_tts.hindi import normalize_hindi, number_to_hindi, script_check
    assert normalize_hindi("सन 1947 में") == "सन उन्नीस सौ सैंतालीस में"
    assert normalize_hindi("2024 में 1,50,000 लोग") == "दो हज़ार चौबीस में एक लाख पचास हज़ार लोग"
    assert normalize_hindi("₹500 और 25%") == "पाँच सौ रुपये और पच्चीस प्रतिशत"
    assert number_to_hindi(123456789) == "बारह करोड़ चौंतीस लाख छप्पन हज़ार सात सौ नवासी"
    assert script_check("Aaj hum ek bahut hi interesting kahani ke baare mein baat karenge") is not None
    assert script_check("आज हम एक कहानी के बारे में बात करेंगे") is None


def test_hindi_sentence_split():
    from omni_tts.text_clean import split_sentences
    assert len(split_sentences("पहला वाक्य। दूसरा वाक्य।", max_chars=12)) == 2


def test_hindi_keeps_paragraphs():
    from omni_tts.hindi import normalize_hindi
    from omni_tts.text_clean import clean_script
    paras = clean_script(normalize_hindi("# ताजमहल की कहानी\n\nसन 1632 में।\n\nदूसरा पैरा।"))
    assert paras == ["ताजमहल की कहानी।", "सन सोलह सौ बत्तीस में।", "दूसरा पैरा।"]


def test_hindi_english_words_and_formats():
    from omni_tts.hindi import normalize_hindi
    assert normalize_hindi("NASA और ISRO का mission") == "नासा और इसरो का मिशन"
    assert normalize_hindi("video को like करें") == "वीडियो को लाइक करें"
    assert normalize_hindi("21वीं सदी में AI") == "इक्कीसवीं सदी में एआई"
    assert normalize_hindi("10:30 बजे 45°C") == "साढ़े दस बजे पैंतालीस डिग्री सेल्सियस"
    assert normalize_hindi("7:15 पर 120 km") == "सात बजकर पंद्रह मिनट पर एक सौ बीस किलोमीटर"
    assert normalize_hindi("[laughter] वाह") == "[laughter] वाह"
    # Veena keeps English words (reads Hinglish natively)
    assert normalize_hindi("video को like करें", english_to_devanagari=False) == "video को like करें"


def test_pronunciation_rules():
    from omni_tts.pronounce import apply, parse
    rules = parse("# comment\nशाहजहाँ = शाह जहाँ\nYouTube = यूट्यूब\nbad line\n")
    assert rules == {"शाहजहाँ": "शाह जहाँ", "YouTube": "यूट्यूब"}
    assert apply("शाहजहाँ ने youtube देखा", rules) == "शाह जहाँ ने यूट्यूब देखा"
    assert apply("शाहजहाँओं", rules) == "शाहजहाँओं"  # whole words only


def test_backup_restore_only_voice_files(tmp_path, monkeypatch):
    import zipfile
    from omni_tts import storage
    monkeypatch.setattr(storage, "VOICES_DIR", tmp_path / "voices")
    z = tmp_path / "b.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("../../evil.txt", "x")
        f.writestr("run.py", "x")
        f.writestr("pronunciations.txt", "a = b")
        f.writestr("folder/me.json", "{}")
        f.writestr("me.pt", "x")
    assert storage.restore_backup(str(z)) == ["me"]
    assert sorted(p.name for p in (tmp_path / "voices").iterdir()) == ["me.json", "me.pt", "pronunciations.txt"]
    assert not (tmp_path.parent / "evil.txt").exists()


def test_music_ducks_under_voice():
    import numpy as np
    from omni_tts.effects import mix_music
    sr = 16000
    voice = np.zeros(6 * sr, np.float32)
    voice[2 * sr:4 * sr] = 0.3 * np.sin(2 * np.pi * 200 * np.arange(2 * sr) / sr)  # speech 2-4 s
    music = np.full(7 * sr, 0.1, np.float32)
    mix = mix_music(voice, sr, music, volume_db=-18, duck_db=8, tail=1.0)
    music_part = mix - np.pad(voice, (0, len(mix) - len(voice)))
    quiet = np.abs(music_part[int(0.5 * sr):int(1.5 * sr)]).mean()
    during = np.abs(music_part[int(2.8 * sr):int(3.2 * sr)]).mean()
    assert during < quiet * 0.5  # at least ~6 dB quieter while the voice speaks


def test_all_styles_run():
    import numpy as np
    from omni_tts.effects import STYLES, apply_style
    sr = 24000
    x = (0.3 * np.sin(2 * np.pi * 150 * np.arange(sr) / sr)).astype(np.float32)
    for name in STYLES:
        y = apply_style(x, sr, name)
        assert len(y) > 0 and not np.isnan(y).any(), name

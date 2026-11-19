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

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

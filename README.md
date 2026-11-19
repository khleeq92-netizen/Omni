# Omni Voiceover Studio

Turn a script (for example one written with ChatGPT) into a professional voiceover, ready for YouTube.

**New here? Read the step-by-step [User Guide](USER_GUIDE.md).**
It is built on the open-source [OmniVoice](https://github.com/k2-fsa/OmniVoice) text-to-speech model.

**What it does to your script**
1. **Cleans it.** It removes Markdown (`#`, `**bold**`, bullets), emojis, links, hashtags, stage directions like `[Dramatic music]` or `(pause)`, labels like `Hook:` or `Narrator:`, and ChatGPT chatter such as "Sure! Here's your script:" or "Let me know if…".
2. **Reads numbers properly**, e.g. "1859" is read as "eighteen fifty-nine" and "3,000" as "three thousand".
3. **Narrates sentence by sentence** in one consistent voice, with natural pauses between sentences and paragraphs.
4. **Masters the audio.** It removes low rumble, sets loudness to -14 LUFS (YouTube's playback level) and limits peaks so the audio never clips.
5. **Exports** a WAV file (48 kHz, 24-bit, for video editors), an MP3 (320 kbps) and the cleaned text.

---

## Option A: Google Colab (free GPU, no installation)

1. Open `Omni_Colab.ipynb` from this repo in [Google Colab](https://colab.research.google.com) (File → Open notebook → GitHub tab).
2. Go to **Runtime → Change runtime type → T4 GPU**.
3. Run the cells in order. The last cell prints a `https://….gradio.live` link. Open it.

## Option B: Your own computer

You need Python 3.10 or newer and ffmpeg. An NVIDIA GPU, or a Mac with an M1–M4 chip, is strongly recommended; on CPU only, it is about 10–30 times slower than real time.

```bash
git clone https://github.com/khleeq92-netizen/Omni.git
```
```bash
cd Omni
```
```bash
python -m venv .venv && source .venv/bin/activate
```
```bash
# NVIDIA GPU (on a Mac, run plain "pip install torch torchaudio" instead)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
```
```bash
pip install -r requirements.txt
```
```bash
python -m omni_tts.app
```
Then open http://127.0.0.1:7860. On Windows, activate the environment with `.venv\Scripts\activate`.

---

## Using the app

**Narrate tab:** paste the script, pick a voice, click **🔊 Preview voice** to hear a short sample, then click **Generate voiceover**, listen and download.
Tick **"Preview with my script's first line"** to hear the voice reading your own text.

**Voices tab:** make the voice the same in every video.
1. **Audition:** pick a preset (or type a description) and generate 3–4 versions.
2. **Lock:** choose the version you like, give it a name (e.g. `my_narrator`) and click **Save voice**.
   It is stored in `voices/` and from then on it sounds identical in every video.
3. **Clone:** upload a 3–10 second clean recording of your own voice, or of someone who has given permission.

### Built-in voice presets
| Preset | Sound | Good for |
|---|---|---|
| `documentary_male` | Deep, calm, British | Documentaries, history |
| `documentary_female` | Warm, authoritative, British | Documentaries |
| `explainer_male` / `explainer_female` | Clear, friendly, American | Facts, explainers, tutorials |
| `storyteller_elder` | Older, slow | Folk tales, stories |
| `deep_trailer` | Very deep, dramatic | Motivation, trailers |
| `mystery_whisper` | Whispered | Horror, mystery |
| `indian_english_male` / `indian_english_female` | Indian-English accent | Indian audience, English scripts |
| `hindi_male` | Hindi, deep and calm | Hindi documentaries, facts |
| `hindi_female` | Hindi, clear and friendly | Hindi explainers |
| `hindi_news` | Hindi, news style | Hindi news, current affairs |
| `hindi_storyteller` | Hindi, older and slow | Kahani, folk tales |
| `hindi_young_male` | Hindi, energetic | Motivation, Shorts |
| `hindi_mystery` | Hindi, whispered | Horror, mystery |

### Hindi narration
- **Write the script in Devanagari** (ask ChatGPT: *"Write this script in Hindi, Devanagari script"*).
  Roman Hindi (Hinglish) is pronounced poorly, and the app warns you if it detects it.
- **Numbers are read the way a Hindi narrator says them:** 1947 → उन्नीस सौ सैंतालीस, 1,50,000 → एक लाख पचास हज़ार, ₹500 → पाँच सौ रुपये, 25% → पच्चीस प्रतिशत.
- **The accent setting only works for English.** For Hindi voices, choose gender, age and pitch instead.

You can also type your own description, combining:
- **gender:** male, female
- **age:** child, teenager, young adult, middle-aged, elderly
- **pitch:** very low, low, moderate, high or very high pitch
- **style:** whisper
- **accent:** american, british, australian, canadian, indian, and others

## Command line
```bash
python -m omni_tts voices
```
```bash
python -m omni_tts narrate my_script.txt --voice documentary_male
```
```bash
python -m omni_tts preview hindi_male
```
```bash
python -m omni_tts audition --preset documentary_male -n 3
```
```bash
python -m omni_tts lock my_narrator --preset documentary_male --seed 2
```
```bash
python -m omni_tts narrate my_script.txt --voice my_narrator --speed 0.95
```
```bash
python -m omni_tts clone my_voice --audio me.wav --text "What I say in the recording."
```
Useful options:
- `--quality draft|fast|high`: draft is quick for checking a script; high gives the best sound.
- `--language en|hi|ur|…`: set the language explicitly.
- `--lufs -16`: a different loudness target, e.g. for podcasts.

## Tips for the best result
- **Write for the ear.** Use short sentences, and spell out unusual names phonetically.
- **Fix a mispronounced English word** with phoneme spelling, e.g. `[B EY1 S] guitar`.
- **Add a reaction sound** with the tags `[laughter]` or `[sigh]`.
- **Lock your voice before making a series**, so every episode sounds the same.
- **English sounds best.** Hindi, Urdu and other languages work, but test them first.

## Responsible use
Only clone voices you own or have written permission to use. Do not imitate real people (celebrities, other creators).
If a video contains realistic synthetic content, follow YouTube's AI-content disclosure rules.

## Project layout
```
omni_tts/text_clean.py   script cleaning and sentence splitting
omni_tts/voices.py       presets and saved voices
omni_tts/engine.py       OmniVoice narration, auditions, voice locking and cloning
omni_tts/mastering.py    pauses, high-pass filter, loudness, limiter, export
omni_tts/app.py          web app (Gradio)
omni_tts/cli.py          command line
Omni_Colab.ipynb         one-click Google Colab notebook
```

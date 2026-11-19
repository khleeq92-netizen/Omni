# Omni Voiceover Studio: User Guide

Turn any script (English or Hindi) into a professional voiceover for YouTube, for free, using Google Colab.

---

## Part 1: Start the app (every time)

You need a Google account. Nothing gets installed on your computer.

### Step 1: Open the notebook
1. Go to **https://colab.research.google.com**
2. Click **File → Open notebook**.
3. Click the **GitHub** tab.
4. Paste `khleeq92-netizen/Omni` and press Enter.
5. Choose the branch `claude/serene-edison-dhp0kf`.
6. Click **Omni_Colab.ipynb**.

### Step 2: Turn on the free GPU
1. In the top menu, click **Runtime → Change runtime type**.
2. Select **T4 GPU**.
3. Click **Save**.

### Step 3: Run everything
1. Close any side panel on the right (click its **✕**).
2. In the top toolbar, click **▷ Run all**.
3. If a pop-up says *"This notebook was not authored by Google"*, click **Run anyway**.

### Step 4: Open the app
1. Wait about 5 minutes. Text scrolls under the cells; this is normal.
2. In the last cell, find this line:
   ```
   Running on public URL: https://xxxxxxxx.gradio.live
   ```
3. Click the **https://….gradio.live** link. The app opens in a new tab.

> ⚠️ Keep the Colab tab open. If you close it, the app stops.
> ⚠️ Don't click the `http://127.0.0.1:7860` link; it doesn't work outside Colab.

---

## Part 2: Make a voiceover

### Step 1: Paste your script
Paste your script into the big **Script** box on the left.
You can paste ChatGPT's answer exactly as it is. The app removes the following on its own:
- Headings (`#`), **bold** markers and bullet points
- Emojis 🌊, links and hashtags
- Stage directions like `[Dramatic music]` or `(pause)`
- Labels like `Hook:`, `Narrator:` or `Scene 1:`
- Chatter like *"Sure! Here's your script:"* and *"Let me know if…"*

### Step 2: Pick a voice
Choose a voice from the **Voice** list (see the voice table in Part 3).

### Step 3: Preview the voice 🔊
Click **🔊 Preview voice** to hear a short sample before converting the whole script.
- Tick **"Preview with my script's first line"** to hear the voice reading your own text.
- Previews you've already heard play instantly the next time.

### Step 4: Adjust (optional)
- **Speed:** `0.9` is slower and calmer, `1.1` is faster.
- **Language:** leave it on *Auto (from voice)*. Hindi voices switch to Hindi on their own.
- **Quality:** `high` gives the best sound, `fast` is quicker, `draft` is for quick checks only.
- **"Or describe a voice":** type your own voice, e.g. `female, elderly, low pitch, british accent`.

### Step 5: Generate and download
1. Click the orange **Generate voiceover** button.
2. Press ▶ on the player to listen.
3. In the **Download** box, click:
   - **.mp3** to share or upload
   - **.wav** for the best quality in a video editor (CapCut, Premiere, DaVinci)

| | Time |
|---|---|
| First voiceover of a session | about 3–5 minutes (the voice model downloads) |
| Every voiceover after that | about 20–60 seconds |

---

## Part 3: Voices

### English voices
| Voice | Sound | Good for |
|---|---|---|
| `documentary_male` | Deep, calm, British | Documentaries, history |
| `documentary_female` | Warm, authoritative, British | Documentaries |
| `explainer_male` | Clear, friendly, American | Facts, explainers |
| `explainer_female` | Bright, clear, American | Facts, tutorials |
| `storyteller_elder` | Older, slow | Stories, folk tales |
| `deep_trailer` | Very deep, dramatic | Motivation, trailers |
| `mystery_whisper` | Whispered | Horror, mystery |
| `indian_english_male` | Indian-English accent | English scripts for an Indian audience |
| `indian_english_female` | Indian-English accent | English scripts for an Indian audience |

### Hindi voices (हिंदी आवाज़ें)
| Voice | Sound | Good for |
|---|---|---|
| `hindi_male` | Deep, calm | Documentaries, facts |
| `hindi_female` | Clear, friendly | Explainers |
| `hindi_news` | News style | News, current affairs |
| `hindi_storyteller` | Older, slow | Kahani, folk tales |
| `hindi_young_male` | Energetic | Motivation, Shorts |
| `hindi_mystery` | Whispered | Horror, mystery |

### Describe your own voice
In the **"Or describe a voice"** box, combine one choice from each group, separated by commas:

| Category | Options |
|---|---|
| Gender | `male`, `female` |
| Age | `child`, `teenager`, `young adult`, `middle-aged`, `elderly` |
| Pitch | `very low pitch`, `low pitch`, `moderate pitch`, `high pitch`, `very high pitch` |
| Style | `whisper` |
| Accent (English scripts only) | `american accent`, `british accent`, `australian accent`, `canadian accent`, `indian accent` |

Example: `male, middle-aged, low pitch, american accent`

---

## Part 4: Keep the same voice in every video ⭐

Preset voices change slightly between runs. For a channel, save one fixed voice:

1. Open the **Voices** tab in the app.
2. Under **1. Audition**, pick a preset (or type a description) and click **Audition**.
3. Listen to the 3 versions.
4. Under **2. Lock your favourite**:
   - In **Version (seed) to keep**, pick the version you liked.
   - Type a **Voice name**, e.g. `my_narrator`.
   - Click **Save voice**.
5. Your voice now appears at the top of the **Voice** list and sounds the same every time.

> 💡 Saved voices are lost when Colab closes, unless you turn on Google Drive. Do this once:
> in the notebook, in the cell `# 2. (Optional)`, change `USE_DRIVE = False` to `USE_DRIVE = True` before you click **Run all**, and allow Drive access when asked.

### Clone your own voice
1. Record **3–10 seconds** of yourself speaking clearly in a quiet room.
2. In the **Voices** tab, under **Clone a voice**, upload the recording and give it a name.
3. Tick the consent box and click **Save cloned voice**.

> ⚠️ Only clone your own voice, or a voice you have written permission to use. Never clone celebrities or other YouTubers.

---

## Part 5: Hindi scripts

1. **Write in Devanagari script, not Roman Hindi.**
   - ✅ `आज हम एक रहस्यमयी कहानी सुनेंगे।`
   - ❌ `Aaj hum ek rahasyamayi kahani sunenge.` (pronounced poorly; the app warns you)
   - Ask ChatGPT: **"Write this YouTube script in Hindi, in Devanagari script."**
2. **Numbers are read the way a Hindi narrator says them:**

   | You write | It says |
   |---|---|
   | 1947 | उन्नीस सौ सैंतालीस |
   | 2024 | दो हज़ार चौबीस |
   | 1,50,000 | एक लाख पचास हज़ार |
   | ₹500 | पाँच सौ रुपये |
   | 25% | पच्चीस प्रतिशत |
   | 3.5 | तीन दशमलव पाँच |
3. **Choose a Hindi voice** (`hindi_male`, `hindi_female` and so on). The language switches to Hindi on its own.
4. **The "accent" setting only works for English.** For Hindi voices, choose gender, age and pitch.

---

## Part 6: Sample scripts to try

### English: quick test (voice `documentary_male`)
```
The Great Wall of China is not one wall. It is thousands of walls, built over more than two thousand years.

Some parts were made of stone and brick. Others were made of packed earth, wood, and even sticky rice mixed into the mortar.

And here is the surprising part. You cannot see it from space with the naked eye. That is one of history's most popular myths.
```

### English: pasted straight from ChatGPT (voice `explainer_female`)
```
Sure! Here's your YouTube script:

# 5 Amazing Facts About the Ocean 🌊

**Hook:**
We have explored less than 25 percent of our own ocean. [Upbeat music]

## Fact 1: The Deepest Point
- The Mariana Trench is about 11,000 meters deep.
- If you dropped Mount Everest inside it, the peak would still be underwater.

Narrator: So next time you take a deep breath, thank the ocean.

Let me know if you want more facts!
```

### English: mystery (voice `mystery_whisper` or `deep_trailer`)
```
In the winter of 1872, a ship called the Mary Celeste was found drifting in the Atlantic Ocean.

Her sails were set. Her cargo was untouched. There was food on the table, and the captain's log was still on his desk.

But there was no one on board. Not a single person.
```

### Hindi: history (voice `hindi_male`)
```
# ताजमहल की कहानी

सन 1632 में शाहजहाँ ने अपनी पत्नी मुमताज़ की याद में ताजमहल बनवाना शुरू किया।

इसे बनाने में लगभग 20,000 कारीगरों ने काम किया। आज हर साल 70 लाख से ज़्यादा लोग इसे देखने आते हैं।
```

### Hindi: mystery (voice `hindi_mystery` or `hindi_storyteller`)
```
राजस्थान में एक गाँव है, जिसका नाम है कुलधरा।

कहा जाता है कि लगभग 200 साल पहले, एक ही रात में पूरा गाँव खाली हो गया।

लोग चले गए, लेकिन अपने घर वैसे ही छोड़ गए। और आज तक कोई नहीं जानता कि उस रात असल में क्या हुआ था।
```

### Hindi: motivation (voice `hindi_young_male`)
```
हर बड़ी सफलता एक छोटे कदम से शुरू होती है।

आप आज जो मेहनत कर रहे हैं, वही कल आपकी पहचान बनेगी।

तो रुकिए मत। गिरिए, उठिए, और फिर से चलिए। क्योंकि जीतने वाले कभी हार नहीं मानते।
```

---

## Part 7: Tips for a professional sound

- **Write for the ear.** Use short sentences, and one idea per sentence.
- **Use blank lines between paragraphs.** The app adds a natural pause there.
- **Add a reaction sound** with `[laughter]` or `[sigh]` in the text.
- **Fix a wrongly pronounced English word** with phoneme spelling, e.g. `[B EY1 S] guitar`.
- **Use the WAV file in your video editor**; it's higher quality than MP3.
- **Volume is set for YouTube already** (-14 LUFS), so you don't need to adjust it.
- **Always edit ChatGPT's script yourself** before using it. YouTube may refuse to pay for mass-produced, unedited AI content.

---

## Part 8: Problems and fixes

| Problem | Fix |
|---|---|
| Cell 1 says **"No GPU"** | Runtime → Change runtime type → **T4 GPU** → Save, then **Run all** again |
| **`cd: Omni: No such file or directory`** | The GitHub repo is private. Make it public on GitHub: Settings → General → Change visibility |
| Colab asks to **Restart session** | Click **Restart**, then click **Run all** again |
| The **gradio.live link stopped working** | Colab disconnected. Click **Run all** again to get a new link |
| **"You cannot connect to a GPU"** | The free GPU limit is reached for today. Try again later, or use Colab Pro |
| **First voiceover is very slow** | Normal: the model downloads once per session (3–5 minutes) |
| **Hindi sounds wrong** | Make sure the script is in Devanagari, and pick a `hindi_…` voice |
| **A word is pronounced wrong** | Spell it the way it sounds, or use phoneme spelling for English |
| **Saved voice disappeared** | Turn on `USE_DRIVE = True` so voices are kept in Google Drive |

---

## Responsible use

- Only clone voices you own or have permission to use.
- Don't imitate real people.
- On YouTube, tick the "altered or synthetic content" box when your video shows realistic AI-made people or events.

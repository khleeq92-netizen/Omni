"""Web app: paste a script, pick a voice, download a finished voiceover.

Run:  python -m omni_tts.app            (local, http://127.0.0.1:7860)
      python -m omni_tts.app --share    (public link, e.g. on Colab)
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

import gradio as gr

from .engine import Narrator
from . import effects, pronounce, storage
from .voices import PRESETS, all_voice_names, list_saved

DESIGN_PRESETS = [n for n, p in PRESETS.items() if p.engine == "omnivoice"]

OUT_DIR = Path("output")
re_deva = re.compile(r"[\u0900-\u097F]")
_narrator: Narrator | None = None


def narrator() -> Narrator:
    global _narrator
    if _narrator is None:
        _narrator = Narrator()
    return _narrator


def _voice_choices() -> list[str]:
    return all_voice_names() + ["auto"]


def _describe(voice: str) -> str:
    from .voices import load_saved
    v = load_saved(voice)
    if v and v.builtin:
        lang = "Hindi" if v.language == "hi" else "English"
        return f"⭐ Ready-made voice ({lang}): {v.description} Sounds identical every time."
    if v:
        return f"Your saved voice ({v.source}), sounds identical every time."
    if voice in PRESETS and PRESETS[voice].engine == "veena":
        return (f"{PRESETS[voice].description} · Fixed voice, sounds the same every time. "
                "Hindi in Devanagari, English, or mixed Hinglish all work. "
                "Note: the first Veena voiceover downloads about 6.5 GB (one time).")
    if voice in PRESETS:
        lang = " · Language: Hindi (write the script in Devanagari)" if PRESETS[voice].language == "hi" else ""
        return f"{PRESETS[voice].description}{lang} · Preset: save it in the Voices tab for full consistency."
    return "Random voice, changes every run."


def do_narrate(script, voice, custom, speed, language, quality, style="natural", music="none",
               music_file=None, music_vol=-18, progress=gr.Progress()):
    if not script or not script.strip():
        raise gr.Error("Paste a script first.")
    voice_arg = custom.strip() if custom and custom.strip() else voice
    stamp = time.strftime("%Y%m%d_%H%M%S")
    first = re.sub(r"[^a-zA-Z0-9]+", "_", script.strip().split("\n")[0])[:40].strip("_")
    base = OUT_DIR / f"{stamp}_{first or 'narration'}"
    n = narrator()
    uses_veena = voice_arg in PRESETS and PRESETS[voice_arg].engine == "veena"
    if uses_veena and n._veena is None:
        progress(0.01, desc="Loading the Veena model (first time after start: 1-3 min; "
                            "first use ever downloads ~6.5 GB)…")
        print("[Omni] Loading Veena model…", flush=True)
        n.veena
    elif not uses_veena and n._model is None:
        progress(0.01, desc="Loading the voice model (first time after start: about 1-2 min)…")
        print("[Omni] Loading voice model…", flush=True)
        n.model
    progress(0.05, desc="Generating… (the first part takes longest)")
    print(f"[Omni] Generating with voice '{voice_arg}'…", flush=True)

    def _progress(d, t):
        progress(0.05 + 0.9 * d / t, desc=f"Generating part {d} of {t}…")
        print(f"[Omni]   part {d}/{t} done", flush=True)

    res = n.narrate(
        script, base, voice=voice_arg, speed=None if speed == 1.0 else speed,
        language=None if language == "auto" else language, quality=quality,
        style=style, music=music, music_file=music_file, music_volume_db=float(music_vol),
        progress=_progress,
    )
    print(f"[Omni] Done: {res.duration_s:.1f} s of audio in {res.elapsed_s:.1f} s → {res.files.get('mp3')}", flush=True)
    info = (f"{res.duration_s:.1f} s of audio, generated in {res.elapsed_s:.1f} s on {n.device}. "
            f"Loudness -14 LUFS (YouTube standard).")
    for w in getattr(n, "warnings", []):
        info += f"\n\n**Note:** {w}"
    files = [str(p) for k, p in res.files.items() if k in ("wav", "mp3")]
    return str(res.files.get("mp3", res.files["wav"])), files, res.text, info


def do_effects(audio_path, style, music, music_file, music_vol):
    """Restyle an existing voiceover: voice style + background music."""
    import soundfile as sf
    from . import mastering
    if not audio_path:
        raise gr.Error("Upload a voiceover first.")
    import librosa
    y, sr = librosa.load(audio_path, sr=48000, mono=True)
    out = effects.process(y, sr, style, music, music_file, float(music_vol))
    out = mastering.master(out, sr)
    base = OUT_DIR / f"{time.strftime('%Y%m%d_%H%M%S')}_styled_{style}_{music}"
    files = mastering.export(out, sr, base)
    return str(files.get("mp3", files["wav"])), [str(p) for p in files.values()]


def do_preview(voice, custom, language, script, use_script):
    voice_arg = custom.strip() if custom and custom.strip() else voice
    text = None
    if use_script and script and script.strip():
        from .text_clean import prepare_script
        paras = prepare_script(script)
        text = paras[0].chunks[0] if paras else None
    path = narrator().preview(voice_arg, None if language == "auto" else language, text)
    return str(path)


def do_audition(preset, custom, count):
    instruct = custom.strip() if custom and custom.strip() else PRESETS[preset].instruct
    lang = PRESETS[preset].language if not (custom and custom.strip()) else "en"
    results = narrator().audition(instruct, OUT_DIR / "auditions" / time.strftime("%H%M%S"),
                                  n=int(count), language=lang)
    outs = [str(p) for _, p in results] + [None] * (4 - len(results))
    seeds = [s for s, _ in results]
    return (*outs[:4], gr.update(choices=seeds, value=seeds[0]), instruct)


def do_lock(name, instruct, seed, speed, preset, custom):
    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", (name or "").strip())
    if not name:
        raise gr.Error("Give the voice a name, e.g. my_narrator")
    if not instruct:
        raise gr.Error("Run an audition first.")
    lang = PRESETS[preset].language if preset in PRESETS and not (custom and custom.strip()) else "en"
    v = narrator().lock_voice(name, instruct, seed=int(seed), speed=float(speed), language=lang)
    return (f"Saved '{v.name}'. It now appears in the voice list.",
            gr.update(choices=_voice_choices(), value=v.name))


def do_clone(name, audio, text, consent, rec_lang="hi"):
    if not consent:
        raise gr.Error("Only clone a voice you own or have written permission to use.")
    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", (name or "").strip())
    if not name or not audio:
        raise gr.Error("Give a name and upload a 3-10 second recording.")
    n = narrator()
    v, info = n.clone_voice(name, audio, (text or "").strip() or None,
                            language=None if rec_lang == "auto" else rec_lang)
    lines = [f"✅ **Saved cloned voice `{v.name}`.** Listen to it below. It is now selected in the Narrate tab."]
    if info["trimmed"]:
        lines.append(f"✂️ Your recording was {info['original_s']} s, so I used the first {info['used_s']} s "
                     "(3–10 s gives the best clone).")
    if info.get("text_dropped"):
        lines.append("ℹ️ The recording was over 20 s, so it was shortened and the typed words were "
                     "replaced by an automatic transcript.")
    if info.get("auto_text"):
        lines.append(f"👂 **Words heard in your recording:** {info['heard']}")
        lines.append("If those words are wrong, type exactly what you said in *What is said in it* "
                     "and click **Save cloned voice** again: correct words give a better clone.")
    else:
        lines.append(f"📝 Used your typed words and the full {info['used_s']} s recording.")
    preview = str(n.preview(v.name))
    import soundfile as sf
    dur = sf.info(preview).duration
    if dur > 22:  # the sample sentence normally takes 8-14 s
        lines.insert(0, "⚠️ **This clone looks broken** (the sample came out far too long). Almost always "
                        "the words don't match the recording: type exactly what is said, or use a "
                        "shorter, clearer recording, and save again.")
    return "\n\n".join(lines), gr.update(choices=_voice_choices(), value=v.name), preview


def do_fill_words(audio, rec_lang):
    if not audio:
        raise gr.Error("Upload or record the audio first.")
    text = narrator().transcribe_file(audio, None if rec_lang == "auto" else rec_lang)
    return text, ("✍️ **Check these words and correct any mistakes**, then click **Save cloned voice**. "
                  "Correct words are the biggest factor in a good clone.")


def build() -> gr.Blocks:
    with gr.Blocks(title="Omni Voiceover Studio") as demo:
        save_status = gr.Markdown(storage.status())
        gr.Markdown("# Omni Voiceover Studio\nPaste your script (Markdown from ChatGPT is fine; "
                    "headings, bullets, emojis and stage directions are cleaned automatically).")
        with gr.Tab("Narrate"):
            with gr.Row():
                with gr.Column(scale=3):
                    script = gr.Textbox(label="Script", lines=16,
                                        placeholder="Paste your script here…")
                with gr.Column(scale=2):
                    voice = gr.Dropdown(_voice_choices(), value=_voice_choices()[0], label="Voice")
                    voice_info = gr.Markdown(_describe(_voice_choices()[0]))
                    with gr.Row():
                        preview_btn = gr.Button("🔊 Preview voice", size="sm")
                        use_script = gr.Checkbox(label="Preview with my script's first line", value=False)
                    preview_player = gr.Audio(label="Voice preview", type="filepath", autoplay=True)
                    custom = gr.Textbox(label="Or describe a voice (optional)",
                                        placeholder="e.g. female, elderly, low pitch, british accent")
                    speed = gr.Slider(0.7, 1.3, value=1.0, step=0.05, label="Speed")
                    language = gr.Dropdown([("Auto (from voice)", "auto"), ("English", "en"), ("Hindi", "hi"),
                                            ("Urdu", "ur"), ("Bengali", "bn"), ("Arabic", "ar"),
                                            ("Spanish", "es"), ("French", "fr"), ("German", "de")],
                                           value="auto", label="Language")
                    quality = gr.Radio(["draft", "fast", "high"], value="high", label="Quality")
                    with gr.Accordion("🎚️ Voice style & background music", open=False):
                        style = gr.Dropdown([(c["label"], k) for k, c in effects.STYLES.items()],
                                            value="natural", label="Voice style")
                        music = gr.Dropdown([(v, k) for k, v in effects.MUSIC.items()], value="none",
                                            label="Background music")
                        music_file = gr.File(label="Your music file (mp3/wav), for 'My own music file'",
                                             file_types=["audio"], type="filepath")
                        music_vol = gr.Slider(-30, -8, value=-18, step=1,
                                              label="Music volume (dB below the voice; lower = quieter)")
                    go = gr.Button("Generate voiceover", variant="primary")
            player = gr.Audio(label="Result", type="filepath")
            downloads = gr.Files(label="Download (WAV 48 kHz/24-bit + MP3 320 kbps)")
            info = gr.Markdown()
            spoken = gr.Textbox(label="Text that was spoken (after cleaning)", lines=6)
            voice.change(_describe, voice, voice_info)
            preview_btn.click(do_preview, [voice, custom, language, script, use_script], preview_player)
            go.click(do_narrate, [script, voice, custom, speed, language, quality,
                                  style, music, music_file, music_vol],
                     [player, downloads, spoken, info])

        with gr.Tab("Voices"):
            gr.Markdown("### 1. Audition\nPick a preset (or describe a voice) and hear a few versions.")
            with gr.Row():
                preset = gr.Dropdown(DESIGN_PRESETS, value="documentary_male", label="Preset")
                a_custom = gr.Textbox(label="Or your own description")
                count = gr.Slider(1, 4, value=3, step=1, label="How many versions")
            a_btn = gr.Button("Audition")
            with gr.Row():
                players = [gr.Audio(label=f"Version {i + 1}", type="filepath") for i in range(4)]
            gr.Markdown("### 2. Lock your favourite\nSaves it so every video uses exactly this voice.")
            used_instruct = gr.Textbox(label="Description used", interactive=False)
            with gr.Row():
                seed = gr.Dropdown([], label="Version (seed) to keep")
                l_name = gr.Textbox(label="Voice name", placeholder="my_narrator")
                l_speed = gr.Slider(0.7, 1.3, value=1.0, step=0.05, label="Default speed")
            l_btn = gr.Button("Save voice", variant="primary")
            l_msg = gr.Markdown()
            a_btn.click(do_audition, [preset, a_custom, count], [*players, seed, used_instruct])
            l_btn.click(do_lock, [l_name, used_instruct, seed, l_speed, preset, a_custom], [l_msg, voice])

            gr.Markdown("### Clone a voice from a recording\nUse your own voice, or one you have permission for.")
            with gr.Row():
                c_name = gr.Textbox(label="Voice name")
                c_audio = gr.Audio(label="3-10 s clean recording", type="filepath")
                with gr.Column():
                    c_text = gr.Textbox(label="Exact words said in the recording (important!)", lines=2)
                    c_fill = gr.Button("✍️ Fill words automatically", size="sm")
                    c_lang = gr.Dropdown([("Hindi", "hi"), ("English", "en"), ("Urdu", "ur"),
                                          ("Auto-detect", "auto")], value="hi",
                                         label="Language of the recording")
            c_consent = gr.Checkbox(label="This is my voice, or I have the speaker's permission")
            c_btn = gr.Button("Save cloned voice", variant="primary")
            c_msg = gr.Markdown()
            c_preview = gr.Audio(label="Your cloned voice (sample)", type="filepath", autoplay=True)
            c_btn.click(do_clone, [c_name, c_audio, c_text, c_consent, c_lang], [c_msg, voice, c_preview])
            c_fill.click(do_fill_words, [c_audio, c_lang], [c_text, c_msg])
            gr.Markdown("### Backup & restore\nDownload your saved voices and pronunciation fixes as one file, "
                        "and upload it again in any later session.")
            with gr.Row():
                b_btn = gr.Button("⬇️ Download backup")
                b_file = gr.File(label="Backup file", interactive=False)
                r_file = gr.File(label="⬆️ Restore: upload a backup .zip", file_types=[".zip"], type="filepath")
            r_msg = gr.Markdown()

            def _restore(path):
                if not path:
                    return "", gr.update()
                names = storage.restore_backup(path)
                msg = f"Restored {len(names)} voice(s): {', '.join(names)}" if names else "No voices found in that file."
                return msg, gr.update(choices=_voice_choices())

            b_btn.click(lambda: str(storage.make_backup()), None, b_file)
            r_file.upload(_restore, r_file, [r_msg, voice])
        with gr.Tab("Effects & Music"):
            gr.Markdown("### Restyle a voiceover you already have\n"
                        "Upload any voiceover (for example one you made earlier), choose a voice style and "
                        "background music, and download the new version. No need to generate it again.\n\n"
                        "Music gets quieter automatically while the voice is speaking. For your own music, "
                        "use tracks you have the rights to (e.g. YouTube Audio Library, Pixabay Music).")
            with gr.Row():
                fx_in = gr.Audio(label="Your voiceover", type="filepath")
                with gr.Column():
                    fx_style = gr.Dropdown([(c["label"], k) for k, c in effects.STYLES.items()],
                                           value="roabdar", label="Voice style")
                    fx_music = gr.Dropdown([(v, k) for k, v in effects.MUSIC.items()], value="electro_pulse",
                                           label="Background music")
                    fx_file = gr.File(label="Your music file (for 'My own music file')",
                                      file_types=["audio"], type="filepath")
                    fx_vol = gr.Slider(-30, -8, value=-18, step=1, label="Music volume (dB below the voice)")
                    fx_go = gr.Button("Apply", variant="primary")
            fx_out = gr.Audio(label="Result", type="filepath")
            fx_files = gr.Files(label="Download")
            fx_go.click(do_effects, [fx_in, fx_style, fx_music, fx_file, fx_vol], [fx_out, fx_files])
        with gr.Tab("Pronunciation"):
            gr.Markdown(
                "### Fix words that are spoken wrongly\n"
                "Write one fix per line as **`word = how to say it`**. Fixes apply to every voiceover, "
                "in every language, and are kept with your saved voices (in Google Drive when it is on).\n\n"
                "Examples: `शाहजहाँ = शाह जहाँ` · `GIF = जिफ़` · `Omni = ओमनी`\n\n"
                "Tip: spell the word in Hindi the way it should *sound*, splitting it with a space if needed.")
            p_text = gr.Textbox(value=pronounce.load_text(), lines=14, label="Your fixes")
            with gr.Row():
                p_save = gr.Button("Save fixes", variant="primary")
                p_try_in = gr.Textbox(label="Test a sentence", placeholder="Type a sentence to see how it will be read")
            p_try_out = gr.Textbox(label="It will be read as", interactive=False)
            p_msg = gr.Markdown()

            def _save(t):
                return f"Saved {pronounce.save_text(t)} fixes."

            def _try(sentence, rules_text, voice_name):
                from .hindi import normalize_hindi
                out = pronounce.apply(sentence or "", pronounce.parse(rules_text))
                p = PRESETS.get(voice_name)
                if p and p.language == "hi" or re_deva.search(out):
                    out = normalize_hindi(out, english_to_devanagari=not (p and p.engine == "veena"))
                return out

            p_save.click(_save, p_text, p_msg)
            p_try_in.submit(_try, [p_try_in, p_text, voice], p_try_out)
    return demo


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--share", action="store_true", help="create a public gradio.live link")
    ap.add_argument("--inbrowser", action="store_true", help="open the app in the browser")
    args = ap.parse_args()

    # Already open (e.g. the app was double-clicked twice)? Just show it.
    if not args.share:
        running = _find_running(args.port)
        if running:
            url = f"http://127.0.0.1:{running}"
            print(f"Omni Studio is already running at {url}. Opening it in the browser.")
            if args.inbrowser:
                import webbrowser
                webbrowser.open(url)
            return

    demo = build().queue()
    last_error = None
    for port in range(args.port, args.port + 20):  # next free port if this one is taken
        try:
            demo.launch(server_name=args.host, server_port=port, share=args.share,
                        inbrowser=args.inbrowser)
            return
        except OSError as e:
            last_error = e
            print(f"Port {port} is busy, trying {port + 1}…")
    raise SystemExit(f"Could not start Omni Studio: {last_error}")


def _find_running(start: int, count: int = 10) -> int | None:
    """Port of an Omni Studio already serving on this computer, if any."""
    import urllib.request
    for port in range(start, start + count):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1) as r:
                if b"Omni Voiceover Studio" in r.read(200_000):
                    return port
        except Exception:
            continue
    return None


if __name__ == "__main__":
    main()

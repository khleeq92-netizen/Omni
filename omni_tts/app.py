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
from .voices import PRESETS, all_voice_names, list_saved

OUT_DIR = Path("output")
_narrator: Narrator | None = None


def narrator() -> Narrator:
    global _narrator
    if _narrator is None:
        _narrator = Narrator()
    return _narrator


def _voice_choices() -> list[str]:
    return all_voice_names() + ["auto"]


def _describe(voice: str) -> str:
    saved = {v.name: v for v in list_saved()}
    if voice in saved:
        return f"Saved voice ({saved[voice].source}), sounds identical every time."
    if voice in PRESETS:
        return f"{PRESETS[voice].description} Preset: lock it in the Voices tab for full consistency."
    return "Random voice, changes every run."


def do_narrate(script, voice, custom, speed, language, quality, progress=gr.Progress()):
    if not script or not script.strip():
        raise gr.Error("Paste a script first.")
    voice_arg = custom.strip() if custom and custom.strip() else voice
    stamp = time.strftime("%Y%m%d_%H%M%S")
    first = re.sub(r"[^a-zA-Z0-9]+", "_", script.strip().split("\n")[0])[:40].strip("_")
    base = OUT_DIR / f"{stamp}_{first or 'narration'}"
    n = narrator()
    res = n.narrate(
        script, base, voice=voice_arg, speed=None if speed == 1.0 and voice_arg in PRESETS else speed,
        language=None if language == "auto" else language, quality=quality,
        progress=lambda d, t: progress(d / t, desc=f"Chunk {d}/{t}"),
    )
    info = (f"{res.duration_s:.1f} s of audio, generated in {res.elapsed_s:.1f} s on {n.device}. "
            f"Loudness -14 LUFS (YouTube standard).")
    files = [str(p) for k, p in res.files.items() if k in ("wav", "mp3")]
    return str(res.files.get("mp3", res.files["wav"])), files, res.text, info


def do_audition(preset, custom, count):
    instruct = custom.strip() if custom and custom.strip() else PRESETS[preset].instruct
    results = narrator().audition(instruct, OUT_DIR / "auditions" / time.strftime("%H%M%S"), n=int(count))
    outs = [str(p) for _, p in results] + [None] * (4 - len(results))
    seeds = [s for s, _ in results]
    return (*outs[:4], gr.update(choices=seeds, value=seeds[0]), instruct)


def do_lock(name, instruct, seed, speed):
    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", (name or "").strip())
    if not name:
        raise gr.Error("Give the voice a name, e.g. my_narrator")
    if not instruct:
        raise gr.Error("Run an audition first.")
    v = narrator().lock_voice(name, instruct, seed=int(seed), speed=float(speed))
    return (f"Saved '{v.name}'. It now appears in the voice list.",
            gr.update(choices=_voice_choices(), value=v.name))


def do_clone(name, audio, text, consent):
    if not consent:
        raise gr.Error("Only clone a voice you own or have written permission to use.")
    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", (name or "").strip())
    if not name or not audio:
        raise gr.Error("Give a name and upload a 3-10 second recording.")
    v = narrator().clone_voice(name, audio, text.strip() or None)
    return f"Saved cloned voice '{v.name}'.", gr.update(choices=_voice_choices(), value=v.name)


def build() -> gr.Blocks:
    with gr.Blocks(title="Omni Voiceover Studio") as demo:
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
                    custom = gr.Textbox(label="Or describe a voice (optional)",
                                        placeholder="e.g. female, elderly, low pitch, british accent")
                    speed = gr.Slider(0.7, 1.3, value=1.0, step=0.05, label="Speed")
                    language = gr.Dropdown(["auto", "en", "hi", "ur", "ar", "es", "fr", "de", "bn"],
                                           value="auto", label="Language")
                    quality = gr.Radio(["draft", "fast", "high"], value="high", label="Quality")
                    go = gr.Button("Generate voiceover", variant="primary")
            player = gr.Audio(label="Result", type="filepath")
            downloads = gr.Files(label="Download (WAV 48 kHz/24-bit + MP3 320 kbps)")
            info = gr.Markdown()
            spoken = gr.Textbox(label="Text that was spoken (after cleaning)", lines=6)
            voice.change(_describe, voice, voice_info)
            go.click(do_narrate, [script, voice, custom, speed, language, quality],
                     [player, downloads, spoken, info])

        with gr.Tab("Voices"):
            gr.Markdown("### 1. Audition\nPick a preset (or describe a voice) and hear a few versions.")
            with gr.Row():
                preset = gr.Dropdown(list(PRESETS), value="documentary_male", label="Preset")
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
            l_btn.click(do_lock, [l_name, used_instruct, seed, l_speed], [l_msg, voice])

            gr.Markdown("### Clone a voice from a recording\nUse your own voice, or one you have permission for.")
            with gr.Row():
                c_name = gr.Textbox(label="Voice name")
                c_audio = gr.Audio(label="3-10 s clean recording", type="filepath")
                c_text = gr.Textbox(label="What is said in it (optional)")
            c_consent = gr.Checkbox(label="This is my voice, or I have the speaker's permission")
            c_btn = gr.Button("Save cloned voice")
            c_msg = gr.Markdown()
            c_btn.click(do_clone, [c_name, c_audio, c_text, c_consent], [c_msg, voice])
    return demo


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--share", action="store_true", help="create a public gradio.live link")
    args = ap.parse_args()
    build().queue().launch(server_name=args.host, server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()

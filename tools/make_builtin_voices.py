"""Create the built-in "impactful male" voices.

For each voice: design 3 variations (seeds), measure each one, and keep the
best as a ready-made saved voice in omni_tts/builtin_voices/.

  * deep   = median pitch (F0) of the sample; lower is deeper
  * clear  = character error rate of a Whisper transcript vs the sample text

A variation must sound male (median F0 < 165 Hz) and be clear; among those,
the deepest wins (clarity breaks near-ties).

Run:  python tools/make_builtin_voices.py [--seeds 3] [--only name1,name2]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from omni_tts.engine import Narrator  # noqa: E402
from omni_tts.voices import BUILTIN_DIR, IMPACT_SAMPLES  # noqa: E402

VOICES = [
    # name, instruct, language, speed, description
    ("deep_narrator_male", "male, middle-aged, very low pitch, american accent", "en", 0.92,
     "Very deep, powerful American narrator: trailers, documentaries, epic stories."),
    ("power_british_male", "male, middle-aged, very low pitch, british accent", "en", 0.93,
     "Deep, commanding British voice: history, documentaries, serious topics."),
    ("motivation_male", "male, young adult, low pitch, american accent", "en", 0.97,
     "Strong, energetic American voice: motivation, sports, Shorts."),
    ("indian_power_male", "male, middle-aged, low pitch, indian accent", "en", 0.95,
     "Deep Indian-English voice with authority: facts, news, explainers."),
    ("hindi_deep_male", "male, middle-aged, very low pitch", "hi", 0.93,
     "Hindi: very deep, powerful narrator for documentaries, history and mystery."),
    ("hindi_power_male", "male, young adult, low pitch", "hi", 0.97,
     "Hindi: strong, energetic voice for motivation, sports and Shorts."),
    ("hindi_legend_male", "male, elderly, very low pitch", "hi", 0.9,
     "Hindi: deep, aged, dramatic voice for kahani, legends and spiritual topics."),
]


def _norm(s: str) -> str:
    return re.sub(r"[\W_]+", "", s.lower())


def cer(ref: str, hyp: str) -> float:
    a, b = _norm(ref), _norm(hyp)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(len(a), 1)


def median_f0(path: Path) -> float:
    import librosa
    y, sr = librosa.load(path, sr=16000)
    f0, voiced, _ = librosa.pyin(y, fmin=50, fmax=400, sr=sr)
    return float(np.nanmedian(f0[voiced])) if np.any(voiced) else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--only", default="")
    ap.add_argument("--work", default="output/builtin_candidates")
    args = ap.parse_args()

    from transformers import pipeline
    asr = pipeline("automatic-speech-recognition", model="openai/whisper-small", device="cpu")
    narrator = Narrator()
    work = Path(args.work)
    only = {n for n in args.only.split(",") if n}
    report = []

    for name, instruct, lang, speed, desc in VOICES:
        if only and name not in only:
            continue
        text = IMPACT_SAMPLES[lang]
        cands = []
        for seed in range(1, args.seeds + 1):
            cname = f"{name}__s{seed}"
            narrator.lock_voice(cname, instruct, seed=seed, speed=speed, language=lang,
                                sample_text=text, directory=work, description=desc)
            wav = work / f"{cname}_sample.wav"
            hyp = asr(str(wav), generate_kwargs={"language": lang})["text"]
            c = {"seed": seed, "f0": round(median_f0(wav), 1), "cer": round(cer(text, hyp), 3),
                 "asr": hyp.strip()}
            cands.append(c)
            print(f"{name} seed{seed}: F0={c['f0']} Hz  CER={c['cer']}  | {c['asr']}", flush=True)

        ok = [c for c in cands if c["f0"] < 165 and c["cer"] <= 0.25] or cands
        best_cer = min(c["cer"] for c in ok)
        pool = [c for c in ok if c["cer"] <= best_cer + 0.08]
        best = min(pool, key=lambda c: c["f0"])
        src = f"{name}__s{best['seed']}"
        BUILTIN_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(work / f"{src}.pt", BUILTIN_DIR / f"{name}.pt")
        shutil.copy(work / f"{src}_sample.wav", BUILTIN_DIR / f"{name}_sample.wav")
        meta = json.loads((work / f"{src}.json").read_text(encoding="utf-8"))
        meta.update(name=name, prompt_path=f"{name}.pt")
        (BUILTIN_DIR / f"{name}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                                  encoding="utf-8")
        report.append({"name": name, "chosen_seed": best["seed"], "candidates": cands})
        print(f"==> {name}: kept seed {best['seed']} (F0 {best['f0']} Hz, CER {best['cer']})", flush=True)

    (work / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

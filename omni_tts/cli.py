"""Command line: python -m omni_tts <command> ...

  narrate   Turn a script (.txt / .md) into a mastered voiceover
  voices    List presets and saved voices
  audition  Generate a few candidate voices for a description
  lock      Save a designed voice so it sounds identical in every video
  clone     Save a voice from a 3-10 s recording (with the speaker's consent)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .voices import PRESETS, list_saved

DESIGN_PRESETS = [n for n, p in PRESETS.items() if p.engine == "omnivoice"]


def _slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", s).strip("_")[:60] or "narration"


def cmd_voices(_args) -> None:
    saved = list_saved()
    print("Saved voices (identical every time):")
    for v in saved:
        print(f"  {v.name:24s} {v.source}  speed={v.speed}")
    if not saved:
        print("  (none yet, create one with: python -m omni_tts lock <name> --preset <preset>)")
    print("\nPresets (voice design, small variation between runs):")
    for p in PRESETS.values():
        print(f"  {p.name:24s} {p.description}  [{p.instruct}]")


def cmd_narrate(args) -> None:
    from .engine import Narrator
    src = Path(args.script)
    script = sys.stdin.read() if args.script == "-" else src.read_text(encoding="utf-8")
    out_dir = Path(args.out)
    base = out_dir / (args.name or _slug(src.stem if args.script != "-" else "narration"))
    narrator = Narrator(device=args.device)
    print(f"Model loaded on {narrator.device}. Narrating with voice '{args.voice}'...")
    res = narrator.narrate(
        script, base, voice=args.voice, speed=args.speed, language=args.language,
        quality=args.quality, seed=args.seed, target_lufs=args.lufs,
        batch_size=args.batch_size, mp3=not args.no_mp3,
        progress=lambda d, t: print(f"  {d}/{t} chunks", flush=True),
    )
    print(f"\nDone: {res.duration_s:.1f}s of audio in {res.elapsed_s:.1f}s ({res.chunks} chunks)")
    for kind, path in res.files.items():
        print(f"  {kind}: {path}")


def cmd_preview(args) -> None:
    from .engine import Narrator
    path = Narrator(device=args.device).preview(args.voice, args.language, args.text)
    print(f"Preview: {path}")


def cmd_audition(args) -> None:
    from .engine import Narrator
    instruct = PRESETS[args.preset].instruct if args.preset else args.instruct
    if not instruct:
        sys.exit("Give --preset or --instruct")
    narrator = Narrator(device=args.device)
    out = Path(args.out)
    for seed, path in narrator.audition(instruct, out, n=args.n, language=args.language):
        print(f"  seed {seed}: {path}")
    print("\nListen, then lock your favourite: python -m omni_tts lock <name> "
          f"--instruct \"{instruct}\" --seed <seed>")


def cmd_lock(args) -> None:
    from .engine import Narrator
    preset = PRESETS.get(args.preset) if args.preset else None
    instruct = args.instruct or (preset.instruct if preset else None)
    if not instruct:
        sys.exit("Give --preset or --instruct")
    speed = args.speed if args.speed is not None else (preset.speed if preset else 1.0)
    narrator = Narrator(device=args.device)
    lang = args.language or (preset.language if preset else "en")
    v = narrator.lock_voice(args.name, instruct, seed=args.seed, speed=speed, language=lang)
    print(f"Saved voice '{v.name}' -> voices/{v.name}.pt (sample: voices/{v.name}_sample.wav)")


def cmd_clone(args) -> None:
    from .engine import Narrator
    narrator = Narrator(device=args.device)
    v = narrator.clone_voice(args.name, args.audio, args.text, speed=args.speed, language=args.language)
    print(f"Saved cloned voice '{v.name}' -> voices/{v.name}.pt")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="omni_tts", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", default=None, help="cuda:0 / mps / cpu (default: auto)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("narrate", help="script -> voiceover")
    n.add_argument("script", help="path to .txt/.md script, or - for stdin")
    n.add_argument("--voice", default="documentary_male",
                   help="saved voice, preset name, 'auto', or a description like 'female, low pitch'")
    n.add_argument("--out", default="output")
    n.add_argument("--name", default=None, help="output file name (default: script name)")
    n.add_argument("--speed", type=float, default=None, help="e.g. 0.9 slower, 1.1 faster")
    n.add_argument("--language", default=None, help="e.g. en, hi, ur (default: auto)")
    n.add_argument("--quality", choices=["draft", "fast", "high"], default="high")
    n.add_argument("--seed", type=int, default=1234)
    n.add_argument("--lufs", type=float, default=-14.0, help="loudness target (YouTube: -14)")
    n.add_argument("--batch-size", type=int, default=4)
    n.add_argument("--no-mp3", action="store_true")
    n.set_defaults(func=cmd_narrate)

    pv = sub.add_parser("preview", help="hear a short sample of a voice")
    pv.add_argument("voice")
    pv.add_argument("--text", default=None)
    pv.add_argument("--language", default=None)
    pv.set_defaults(func=cmd_preview)

    v = sub.add_parser("voices", help="list voices")
    v.set_defaults(func=cmd_voices)

    a = sub.add_parser("audition", help="try candidate voices for a description")
    a.add_argument("--preset", choices=DESIGN_PRESETS)
    a.add_argument("--instruct")
    a.add_argument("-n", type=int, default=3)
    a.add_argument("--language", default=None, help="default: the preset's language")
    a.add_argument("--out", default="output/auditions")
    a.set_defaults(func=cmd_audition)

    lk = sub.add_parser("lock", help="save a designed voice permanently")
    lk.add_argument("name")
    lk.add_argument("--preset", choices=DESIGN_PRESETS)
    lk.add_argument("--instruct")
    lk.add_argument("--seed", type=int, default=1)
    lk.add_argument("--speed", type=float, default=None)
    lk.add_argument("--language", default=None, help="default: the preset's language")
    lk.set_defaults(func=cmd_lock)

    c = sub.add_parser("clone", help="save a voice from a recording (consent required)")
    c.add_argument("name")
    c.add_argument("--audio", required=True, help="3-10 s clean recording")
    c.add_argument("--text", default=None, help="what is said in the recording (default: auto-transcribe)")
    c.add_argument("--speed", type=float, default=1.0)
    c.add_argument("--language", default=None)
    c.set_defaults(func=cmd_clone)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

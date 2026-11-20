"""Where your voices are kept, plus backup / restore as a zip file."""

from __future__ import annotations

import time
import zipfile
from pathlib import Path

from .voices import VOICES_DIR

_ALLOWED = {".json", ".pt", ".wav", ".txt"}


def status() -> str:
    """One line telling the user whether saved voices survive a restart."""
    real = VOICES_DIR.resolve()
    if str(real).startswith("/content/drive"):
        return ("✅ **Your voices and fixes are saved in Google Drive** (My Drive → Omni). "
                "They will still be here next time.")
    if Path("/content").exists():  # running on Colab without Drive
        return ("⚠️ **Your saved and cloned voices are NOT kept after Colab closes.** "
                "Turn on Google Drive in the notebook (cell 2, `USE_DRIVE = True`), "
                "or use **Download backup** in the Voices tab before closing.")
    return f"💾 Your voices are saved on this computer in `{VOICES_DIR}`."


def make_backup(out_dir: Path = Path("output")) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"omni_voices_backup_{time.strftime('%Y%m%d_%H%M')}.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        if VOICES_DIR.exists():
            for f in sorted(VOICES_DIR.iterdir()):
                if f.is_file() and f.suffix in _ALLOWED:
                    z.write(f, f.name)
    return path


def restore_backup(zip_path: str) -> list[str]:
    """Restore voices from a backup zip. Returns the names of restored voices."""
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    restored = []
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            name = Path(info.filename).name  # ignore any folders in the zip
            if info.is_dir() or not name or Path(name).suffix not in _ALLOWED:
                continue
            if name.endswith(".txt") and name != "pronunciations.txt":
                continue
            if info.file_size > 50 * 1024 * 1024:
                continue
            (VOICES_DIR / name).write_bytes(z.read(info))
            if name.endswith(".json"):
                restored.append(Path(name).stem)
    return restored

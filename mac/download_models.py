"""Download the voice model used by Omni Studio (about 3 GB).

Optional models are NOT downloaded here, to save disk space; they download
automatically the first time they are used:
  * Veena Hindi voices (veena_*)       about 6.5 GB
  * "Fill words automatically" (Whisper) about 1.6 GB
Pass --all to download them now as well.
"""

import sys

from huggingface_hub import snapshot_download

REQUIRED = ["k2-fsa/OmniVoice"]
OPTIONAL = ["maya-research/Veena", "hubertsiuzdak/snac_24khz", "openai/whisper-large-v3-turbo"]

repos = REQUIRED + (OPTIONAL if "--all" in sys.argv else [])
for repo in repos:
    print(f"Downloading {repo} ...", flush=True)
    for attempt in range(3):
        try:
            snapshot_download(repo)
            break
        except Exception as e:  # flaky Wi-Fi: retry, downloads resume
            print(f"  retrying ({e})", flush=True)
    else:
        sys.exit(f"Could not download {repo}. Check the internet connection and run the installer again.")
print("Models ready.")

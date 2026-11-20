#!/bin/bash
# Starts Omni Studio and opens it in the browser. Close this window to quit.
HOME_DIR="${OMNI_INSTALL_DIR:-$HOME/OmniStudio}"
DATA_DIR="${OMNI_DATA_DIR:-$HOME/Documents/Omni Studio}"
export OMNI_VOICES_DIR="$DATA_DIR/voices"
export GRADIO_ANALYTICS_ENABLED=False
export PYTORCH_ENABLE_MPS_FALLBACK=1   # run any op the Mac GPU lacks on the CPU instead of failing
export TOKENIZERS_PARALLELISM=false

# Work offline when there is no internet (everything needed is already downloaded).
if ! curl -s -m 3 -o /dev/null https://huggingface.co; then
  export HF_HUB_OFFLINE=1
  echo "No internet: running offline."
fi

mkdir -p "$DATA_DIR/voices" "$DATA_DIR/output"
cd "$DATA_DIR" || exit 1
clear
echo "======================================================"
echo "  Omni Studio is starting... your browser will open."
echo "  Keep this window open while you work."
echo "  To quit: close this window (or press Ctrl+C)."
echo "======================================================"
PYTHONPATH="$HOME_DIR/app" exec "$HOME_DIR/venv/bin/python" -m omni_tts.app --inbrowser

#!/bin/bash
# Omni Studio installer for Apple Silicon Macs (M1-M4).
#
# Run in Terminal:
#   curl -fsSL https://raw.githubusercontent.com/khleeq92-netizen/Omni/claude/serene-edison-dhp0kf/mac/install.sh | bash
#
# Installs into ~/OmniStudio (program) and ~/Documents/Omni Studio (your voices
# and voiceovers), then adds "Omni Studio" to Applications. Running it again
# updates the program and keeps your voices. About 5 GB.
set -euo pipefail

BRANCH="claude/serene-edison-dhp0kf"
ZIP_URL="https://codeload.github.com/khleeq92-netizen/Omni/zip/refs/heads/${BRANCH}"
HOME_DIR="${OMNI_INSTALL_DIR:-$HOME/OmniStudio}"
DATA_DIR="${OMNI_DATA_DIR:-$HOME/Documents/Omni Studio}"
APP_DIR="$HOME_DIR/app"
VENV="$HOME_DIR/venv"

say()  { printf "\n\033[1;34m==> %s\033[0m\n" "$1"; }
fail() { printf "\n\033[1;31mError: %s\033[0m\n" "$1"; exit 1; }

if [ "${OMNI_TEST_MODE:-0}" != "1" ]; then
  [ "$(uname -s)" = "Darwin" ] || fail "This installer is for macOS."
  [ "$(uname -m)" = "arm64" ] || fail "This needs an Apple Silicon Mac (M1, M2, M3 or M4)."
fi

free_gb=$(df -g "$HOME" 2>/dev/null | awk 'NR==2 {print $4}' || echo 99)
if [ -n "$free_gb" ] && [ "$free_gb" -lt 8 ] 2>/dev/null; then
  fail "Only ${free_gb} GB free. Omni Studio needs about 6 GB (8 GB free recommended)."
fi

say "Step 1/5: Getting the Python tool manager (uv)"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv >/dev/null 2>&1 || fail "Could not install uv. Check your internet connection and try again."

say "Step 2/5: Downloading Omni Studio"
mkdir -p "$HOME_DIR" "$DATA_DIR/voices" "$DATA_DIR/output"
tmp=$(mktemp -d)
curl -fsSL "$ZIP_URL" -o "$tmp/omni.zip" || fail "Download failed. Check your internet connection."
unzip -q "$tmp/omni.zip" -d "$tmp"
src=$(find "$tmp" -maxdepth 1 -type d -name "Omni-*" | head -1)
[ -n "$src" ] || fail "Downloaded file looks wrong."
rm -rf "$APP_DIR"
mv "$src" "$APP_DIR"
rm -rf "$tmp"

say "Step 3/5: Installing Python and libraries (about 1.5 GB, a few minutes)"
[ -x "$VENV/bin/python" ] || uv venv --python 3.12 "$VENV"
VIRTUAL_ENV="$VENV" uv pip install --python "$VENV/bin/python" -r "$APP_DIR/mac/requirements-mac.txt"

say "Step 4/5: Downloading the voice model (about 3 GB, one time only)"
"$VENV/bin/python" "$APP_DIR/mac/download_models.py"

say "Step 5/5: Creating the Omni Studio app"
cp "$APP_DIR/mac/start.sh" "$HOME_DIR/start.sh"
cp "$APP_DIR/mac/uninstall.sh" "$HOME_DIR/uninstall.sh"
chmod +x "$HOME_DIR/start.sh" "$HOME_DIR/uninstall.sh"
if [ "$(uname -s)" = "Darwin" ]; then
  target="/Applications"
  [ -w "$target" ] || { target="$HOME/Applications"; mkdir -p "$target"; }
  rm -rf "$target/Omni Studio.app"
  osacompile -o "$target/Omni Studio.app" \
    -e "tell application \"Terminal\"" \
    -e "  activate" \
    -e "  do script \"'$HOME_DIR/start.sh'\"" \
    -e "end tell"
  app_path="$target/Omni Studio.app"
else
  app_path="(test mode: no app created)"
fi

say "Done! 🎉"
cat <<EOF

  Open Omni Studio:  double-click "Omni Studio" in your Applications folder
                     (or press Cmd+Space and type "Omni Studio").
  It opens in your browser at http://127.0.0.1:7860
  To quit:           close the Terminal window that opens with it.

  Your voices and voiceovers:  $DATA_DIR
  App:                         $app_path
  Update later:      run the same install command again (your voices are kept).
  Uninstall:         $HOME_DIR/uninstall.sh

EOF

if [ "${OMNI_TEST_MODE:-0}" != "1" ] && [ "${OMNI_NO_LAUNCH:-0}" != "1" ]; then
  open "$app_path"
fi

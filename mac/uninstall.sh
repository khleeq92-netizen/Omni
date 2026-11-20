#!/bin/bash
# Removes Omni Studio and its downloaded models. Your voices and voiceovers in
# ~/Documents/Omni Studio are kept unless you choose to delete them.
HOME_DIR="${OMNI_INSTALL_DIR:-$HOME/OmniStudio}"
DATA_DIR="${OMNI_DATA_DIR:-$HOME/Documents/Omni Studio}"
HF="$HOME/.cache/huggingface/hub"

echo "This removes the Omni Studio program and its voice models."
read -r -p "Continue? (y/n) " ok
[ "$ok" = "y" ] || exit 0

rm -rf "/Applications/Omni Studio.app" "$HOME/Applications/Omni Studio.app"
for m in models--k2-fsa--OmniVoice models--maya-research--Veena models--hubertsiuzdak--snac_24khz \
         models--openai--whisper-large-v3-turbo; do
  rm -rf "${HF:?}/$m"
done
rm -rf "$HOME/.cache/wetextprocessing"

read -r -p "Also delete your saved voices and voiceovers in '$DATA_DIR'? (y/n) " del
[ "$del" = "y" ] && rm -rf "$DATA_DIR"

rm -rf "$HOME_DIR"
echo "Omni Studio has been removed."

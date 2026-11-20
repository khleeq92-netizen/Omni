# Omni Studio on your Mac (offline)

For **Apple Silicon Macs** (M1, M2, M3, M4) with macOS 14 or newer.
No Colab, no Kaggle, no GPU limits, no changing links. After the one-time setup, it works without internet.

---

## One-time setup (about 15–30 minutes, mostly downloading)

1. Open **Terminal**: press **⌘ Cmd + Space**, type `Terminal`, press **Enter**.
2. Copy this whole line, paste it into Terminal (**⌘ Cmd + V**) and press **Enter**:

```bash
curl -fsSL https://raw.githubusercontent.com/khleeq92-netizen/Omni/claude/serene-edison-dhp0kf/mac/install.sh | bash
```

3. Wait until it says **Done! 🎉**. It shows 5 steps as it goes. Keep the Mac awake and connected to the internet.
4. Omni Studio opens by itself. If macOS asks *"Omni Studio wants to control Terminal"*, click **OK** (this is how the app starts).

**Disk space:** about **5 GB**. Two optional parts download only the first time you use them:
- Veena Hindi voices (`veena_…`): about 6.5 GB
- **✍️ Fill words automatically** (in Clone): about 1.6 GB

---

## Every day

1. Open **Omni Studio** from **Applications**, or press **⌘ Space** and type `Omni Studio`.
   Tip: right-click its icon in the Dock → **Options → Keep in Dock**.
2. A Terminal window opens, then your browser opens the studio (first start takes about 30–60 seconds).
3. Use it exactly as before: **Narrate**, **Voices**, **Effects & Music**, **Pronunciation**.
4. **To quit:** close the Terminal window.

## Where are my files?
In **Finder → Documents → Omni Studio**:
- `voices` holds your cloned and saved voices and your pronunciation fixes
- `output` holds every voiceover you've made (WAV + MP3)

These stay on your Mac permanently. To be extra safe, use **Voices → ⬇️ Download backup** now and then.

## Update to the newest version
Run the same Terminal command again. Your voices and voiceovers are kept.

## Uninstall
In Terminal:
```bash
~/OmniStudio/uninstall.sh
```
It asks before deleting your voices.

---

## Good to know
- **Speed:** the Mac's built-in GPU does the work. OmniVoice voices should be quick. Veena voices are slower
  (a 3-billion-parameter model), roughly a few minutes per minute of audio.
- **Memory:** with 16 GB of RAM, close heavy apps when using Veena voices.
- **Numbers in English** are read with a Mac-compatible reader (e.g. 1859 is read as "eighteen fifty-nine").

## Problems
| Problem | Fix |
|---|---|
| `zsh: command not found: curl` | Very unlikely on macOS. Restart the Mac and try again |
| Stops with "Download failed" | Check Wi-Fi and run the command again; it continues where it stopped |
| The browser didn't open | Open **http://127.0.0.1:7860** yourself |
| "Cannot find empty port" / "Address already in use" | An old copy is still running. Paste `pkill -f omni_tts.app` in Terminal, then open Omni Studio again (newer versions do this automatically) |
| "Omni Studio can't be opened" | Run the install command again |
| Veena says it needs a download | Connect to the internet once and try again |

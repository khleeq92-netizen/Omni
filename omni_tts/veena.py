"""Veena (Maya Research): a Hindi/English TTS model trained on Indian speech.

Apache-2.0, https://huggingface.co/maya-research/Veena. A 3B Llama-style model
that writes SNAC audio codes; it reads Hindi, English and mixed Hinglish
natively. Four built-in speakers, no cloning.
"""

from __future__ import annotations

import numpy as np

MODEL_ID = "maya-research/Veena"
SNAC_ID = "hubertsiuzdak/snac_24khz"
SAMPLE_RATE = 24000
SPEAKERS = ["kavya", "agastya", "maitri", "vinaya"]

# Fixed control tokens from the model card.
START_OF_SPEECH = 128257
END_OF_SPEECH = 128258
START_OF_HUMAN = 128259
END_OF_HUMAN = 128260
START_OF_AI = 128261
END_OF_AI = 128262
AUDIO_BASE = 128266


class VeenaEngine:
    def __init__(self, device: str | None = None):
        import torch
        from snac import SNAC
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if device is None:
            device = "cuda:0" if torch.cuda.is_available() else (
                "mps" if torch.backends.mps.is_available() else "cpu")
        self.device = device
        # fp16 on GPU (T4 has no fast bf16); bf16 on CPU halves RAM use.
        dtype = torch.bfloat16 if device == "cpu" else torch.float16
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, dtype=dtype, device_map=device).eval()
        self.snac = SNAC.from_pretrained(SNAC_ID).eval().to(device)

    def generate(self, text: str, speaker: str = "kavya", temperature: float = 0.4,
                 top_p: float = 0.9, seed: int | None = None) -> np.ndarray:
        import torch
        if speaker not in SPEAKERS:
            raise ValueError(f"Unknown Veena speaker {speaker!r}; choose from {SPEAKERS}")
        if seed is not None:
            torch.manual_seed(seed)
        prompt = self.tokenizer.encode(f"<spk_{speaker}> {text}", add_special_tokens=False)
        ids = [START_OF_HUMAN, *prompt, END_OF_HUMAN, START_OF_AI, START_OF_SPEECH]
        # ~7 codes per 85 ms frame; leave headroom inside the 2048-token context.
        max_new = min(int(len(text) * 1.3) * 7 + 21, 2048 - len(ids) - 8)
        with torch.no_grad():
            out = self.model.generate(
                torch.tensor([ids], device=self.model.device),
                max_new_tokens=max_new, do_sample=True, temperature=temperature,
                top_p=top_p, repetition_penalty=1.05,
                pad_token_id=self.tokenizer.pad_token_id or END_OF_AI,
                eos_token_id=[END_OF_SPEECH, END_OF_AI],
            )
        gen = out[0][len(ids):].tolist()
        codes = [t for t in gen if AUDIO_BASE <= t < AUDIO_BASE + 7 * 4096]
        codes = codes[: len(codes) // 7 * 7]
        if not codes:
            raise RuntimeError("Veena produced no audio for this text")
        return self._decode(codes)

    def _decode(self, codes: list[int]) -> np.ndarray:
        import torch
        lv = [[], [], []]
        off = [AUDIO_BASE + i * 4096 for i in range(7)]
        for i in range(0, len(codes), 7):
            c = codes[i:i + 7]
            lv[0].append(c[0] - off[0])
            lv[1] += [c[1] - off[1], c[4] - off[4]]
            lv[2] += [c[2] - off[2], c[3] - off[3], c[5] - off[5], c[6] - off[6]]
        dev = next(self.snac.parameters()).device
        tensors = [torch.tensor(x, dtype=torch.int32, device=dev).unsqueeze(0).clamp(0, 4095)
                   for x in lv]
        with torch.no_grad():
            audio = self.snac.decode(tensors)
        return audio.squeeze().clamp(-1, 1).float().cpu().numpy()

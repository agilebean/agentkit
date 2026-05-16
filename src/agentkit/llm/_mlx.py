"""Local LLM text generation using MLX Qwen models on Apple Silicon."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if not TYPE_CHECKING:
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

_MODELS = Path.home() / ".lmstudio" / "models"

MODEL_VARIANTS = {
    "qwen3": str(_MODELS / "lmstudio-community" / "Qwen3-4B-Instruct-2507-MLX-4bit"),
    "0.8b": str(_MODELS / "mlx-community" / "Qwen3.5-0.8B-MLX-4bit"),
    "2b": str(_MODELS / "mlx-community" / "Qwen3.5-2B-MLX-4bit"),
    "4b": str(_MODELS / "mlx-community" / "Qwen3.5-4B-MLX-4bit"),
}

_VLM_PATTERNS = ("3.5", "qwen3.5")

DEFAULT_MODEL_PATH = MODEL_VARIANTS["2b"]


class MlxLlm:
    """Wrapper around an MLX language model.

    For Qwen3.5 (multimodal) models, weights are loaded with ``strict=False``
    so vision-tower parameters are silently skipped; text generation works
    normally.  Auto-detected from the model path.
    """

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self._use_vlm = _is_vlm(self.model_path)
        self.model = None
        self.tokenizer = None
        self.last_prompt_tokens: int = 0
        self.last_gen_tokens: int = 0

    def load(self):
        """Lazy-load model and tokenizer (call once, reuse across turns)."""
        if self.model is not None:
            return

        from mlx_lm.utils import load_model, load_tokenizer

        model_path = Path(self.model_path)
        if self._use_vlm:
            self.model, _ = load_model(model_path, strict=False)
        else:
            self.model, _ = load_model(model_path)

        self.tokenizer = load_tokenizer(model_path)

    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 80,
        temp: float = 0.7,
    ) -> str:
        """Generate text from chat messages in OpenAI format.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            max_tokens: Maximum tokens to generate.
            temp: Sampling temperature (0.0–1.0).

        Returns:
            Generated text string.
        """
        if self.model is None:
            self.load()

        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        self.last_prompt_tokens = len(self.tokenizer.encode(prompt))
        sampler = make_sampler(temp=temp, min_p=0.05, top_k=50)
        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=sampler,
        )
        response = response.strip()
        self.last_gen_tokens = len(self.tokenizer.encode(response))
        return response


def _is_vlm(model_path: str) -> bool:
    """Detect Qwen3.5 VLM variants from model path for strict=False loading."""
    lower = model_path.lower()
    return any(p in lower for p in _VLM_PATTERNS)

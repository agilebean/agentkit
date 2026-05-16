"""Tests for agentkit.llm.mlx — import checks only (no model loading)."""
import pytest

from agentkit.llm import MlxLlm, MODEL_VARIANTS, DEFAULT_MODEL_PATH
from agentkit.llm._mlx import _is_vlm


class TestMlxLlm:
    def test_constructor_defaults(self):
        llm = MlxLlm()
        assert llm.model_path == DEFAULT_MODEL_PATH
        assert llm.last_prompt_tokens == 0
        assert llm.last_gen_tokens == 0

    def test_constructor_custom_path(self):
        llm = MlxLlm(model_path="/custom/path")
        assert llm.model_path == "/custom/path"

    def test_model_variants_dict(self):
        assert "qwen3" in MODEL_VARIANTS
        assert "2b" in MODEL_VARIANTS
        assert "4b" in MODEL_VARIANTS
        assert "0.8b" in MODEL_VARIANTS


class TestVlmDetection:
    def test_detects_qwen3_5(self):
        assert _is_vlm("/models/Qwen3.5-2B-MLX-4bit")

    def test_detects_0_8b(self):
        assert _is_vlm("/models/qwen3.5-0.8b-mlx")

    def test_non_vlm_passes(self):
        assert not _is_vlm("/models/Qwen3-4B-Instruct")

    def test_default_model_is_vlm(self):
        llm = MlxLlm()
        assert llm._use_vlm is True  # DEFAULT is Qwen3.5-2B

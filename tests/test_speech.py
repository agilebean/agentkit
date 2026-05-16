"""Tests for agentkit.speech — import checks only (no model loading)."""
import pytest

from agentkit.speech import (
    MlxTts,
    MlxStt,
    KOKORO_MODEL_ID,
    KOKORO_VOICES,
    KOKORO_DEFAULT_VOICE,
    KOKORO_VOICE_DESCRIPTIONS,
)


class TestMlxTts:
    def test_constructor(self):
        tts = MlxTts()
        assert tts.model is None

    def test_constants(self):
        assert "mlx-community/Kokoro-82M-bf16" in KOKORO_MODEL_ID
        assert "af_heart" in KOKORO_VOICES
        assert KOKORO_DEFAULT_VOICE in KOKORO_VOICES

    def test_voice_descriptions(self):
        for voice in KOKORO_VOICES:
            assert voice in KOKORO_VOICE_DESCRIPTIONS


class TestMlxStt:
    def test_constructor(self):
        stt = MlxStt()
        assert stt._model is None

    def test_default_model(self):
        assert "parakeet" in MlxStt.DEFAULT_MODEL.lower()

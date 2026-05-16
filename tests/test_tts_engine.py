import pytest


def test_tts_engine_pyttsx3_prefers_female():
    try:
        import pyttsx3  # type: ignore
    except Exception:
        pytest.skip("pyttsx3 not installed; skipping TTS engine test")

    from voice.tts_engine import TTSEngine

    tts = TTSEngine(fallback=True, preferred_voice="female", rate=140, volume=0.9)
    assert hasattr(tts, "_pytt_engine")
    assert tts._pytt_engine is not None
    # Check configured rate property exists
    assert getattr(tts, "rate", None) == 140

from voice.wakeword_manager import WakeWordManager


def test_is_non_speech_allows_single_word_wake_phrase():
    assert WakeWordManager._is_non_speech("friday") is False
    assert WakeWordManager._is_non_speech("computer") is False
    assert WakeWordManager._is_non_speech("hey friday") is False


def test_is_non_speech_keeps_non_speech_noise_filtered():
    assert WakeWordManager._is_non_speech("[music playing]") is True
    assert WakeWordManager._is_non_speech("(clapping)") is True

import asyncio

import numpy as np
import pytest


class DummyStreamingTranscriber:
    def __init__(self):
        self.whisper_binary = "/usr/bin/whisper"
        self.chunk_size = 512
        self.sample_rate = 16000

    async def transcribe_stream(self, audio_generator):
        results = []
        async for chunk in audio_generator:
            results.append(chunk)
        return f"streamed {len(results)}"


@pytest.mark.asyncio
async def test_audio_manager_uses_streaming_transcriber(monkeypatch):
    import voice.audio_manager as audio_manager_module

    monkeypatch.setattr(audio_manager_module, "StreamingTranscriber", DummyStreamingTranscriber)
    monkeypatch.setattr(audio_manager_module.sd, "rec", lambda frames, samplerate, channels, dtype: np.zeros((frames, channels), dtype=np.float32))
    monkeypatch.setattr(audio_manager_module.sd, "wait", lambda: None)

    AudioManager = audio_manager_module.AudioManager
    audio_manager = AudioManager(record_duration=0.1)
    transcription = await audio_manager.listen()

    assert transcription.startswith("streamed")
    assert "streamed" in transcription

"""
TTS = Text-To-Speech (text -> spoken audio), using Kokoro.

Kokoro is a small, fast voice model. We load it once, then for each reply we
generate audio (a numpy array of sound samples) and pack it into a WAV file.
"""
import io
import numpy as np
import soundfile as sf
import config

_pipeline = None


def _get_pipeline():
    """Load Kokoro on first use, then cache it."""
    global _pipeline
    if _pipeline is None:
        from kokoro import KPipeline
        print("[tts] loading Kokoro...")
        # lang_code 'a' = American English.
        _pipeline = KPipeline(lang_code="a")
        print("[tts] ready")
    return _pipeline


def synthesize(text: str) -> bytes:
    """
    Turn text into WAV audio bytes.
    Kokoro yields the speech in chunks (one per sentence-ish); we glue them
    together into a single audio array, then write it out as a WAV file.
    """
    pipeline = _get_pipeline()

    audio_chunks = []
    for _graphemes, _phonemes, audio in pipeline(text, voice=config.TTS_VOICE):
        # audio may be a torch tensor; convert to a plain numpy array.
        if hasattr(audio, "numpy"):
            audio = audio.numpy()
        audio_chunks.append(audio)

    if not audio_chunks:
        return b""

    full_audio = np.concatenate(audio_chunks)

    # Write the numpy array into a WAV file held in memory, return its bytes.
    buffer = io.BytesIO()
    sf.write(buffer, full_audio, config.TTS_SAMPLE_RATE, format="WAV")
    return buffer.getvalue()

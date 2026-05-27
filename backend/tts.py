"""
TTS = Text-To-Speech (text -> spoken audio), using Kokoro.

Kokoro is a small, fast voice model. It needs a different "pipeline" per
language (Kokoro lang codes: "a" = US English, "h" = Hindi). We cache one
pipeline per language and pick the voice based on the language the user spoke.
"""
import io
import numpy as np
import soundfile as sf
import config

# Map our language codes (from Whisper) -> Kokoro (lang_code, voice).
_LANG_MAP = {
    "hi": ("h", config.TTS_VOICE_HI),
    "en": ("a", config.TTS_VOICE_EN),
}

_pipelines = {}  # cache: kokoro lang_code -> KPipeline


def _get_pipeline(kokoro_lang: str):
    """Load (and cache) a Kokoro pipeline for a given language code."""
    if kokoro_lang not in _pipelines:
        from kokoro import KPipeline
        print(f"[tts] loading Kokoro pipeline for lang '{kokoro_lang}'...")
        _pipelines[kokoro_lang] = KPipeline(lang_code=kokoro_lang)
        print("[tts] ready")
    return _pipelines[kokoro_lang]


def synthesize(text: str, lang: str = "en") -> bytes:
    """
    Turn text into WAV audio bytes, using a voice that matches `lang`
    (the language Whisper detected). Anything that isn't Hindi falls back
    to English.
    """
    kokoro_lang, voice = _LANG_MAP.get(lang, _LANG_MAP["en"])
    pipeline = _get_pipeline(kokoro_lang)

    audio_chunks = []
    for _graphemes, _phonemes, audio in pipeline(text, voice=voice):
        if hasattr(audio, "numpy"):
            audio = audio.numpy()
        audio_chunks.append(audio)

    if not audio_chunks:
        return b""

    full_audio = np.concatenate(audio_chunks)

    buffer = io.BytesIO()
    sf.write(buffer, full_audio, config.TTS_SAMPLE_RATE, format="WAV")
    return buffer.getvalue()

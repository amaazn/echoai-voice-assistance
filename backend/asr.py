"""
ASR = Automatic Speech Recognition (speech -> text), using faster-whisper.

We load the model ONCE and reuse it for every request, the same way you'd
open a DB connection at startup instead of on every API call.
"""
import io
from faster_whisper import WhisperModel
import config

_model = None  # the loaded model lives here (a module-level singleton)


def _get_model():
    """Load the Whisper model on first use, then cache it."""
    global _model
    if _model is None:
        print(f"[asr] loading Whisper '{config.ASR_MODEL}' on {config.ASR_DEVICE}...")
        _model = WhisperModel(
            config.ASR_MODEL,
            device=config.ASR_DEVICE,
            compute_type=config.ASR_COMPUTE,
        )
        print("[asr] ready")
    return _model


def transcribe(audio_bytes: bytes) -> str:
    """
    Take raw audio bytes (the .webm Blob from the browser) and return text.
    faster-whisper decodes the audio internally (it uses ffmpeg under the hood).
    """
    model = _get_model()
    segments, _info = model.transcribe(
        io.BytesIO(audio_bytes),  # wrap bytes as a file-like object
        language="en",            # force English; remove to auto-detect
        beam_size=1,              # beam_size=1 is fastest (greedy) = lower latency
        vad_filter=True,          # skip silence -> faster + cleaner transcript
    )
    text = "".join(seg.text for seg in segments).strip()
    return text

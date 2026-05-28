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


def transcribe(audio_bytes: bytes, language: str | None = None) -> tuple[str, str]:
    """
    Take raw audio bytes (the .webm Blob from the browser) and return (text, language).
    If `language` is given ("en"/"hi"), we FORCE Whisper to that language — far more
    reliable than auto-detect, which often guesses wrong on short clips.

    We also tune decoding per language: Hindi gets a wider beam + a Devanagari
    priming prompt, which measurably improves accuracy. English stays on the fast
    greedy path because Whisper is already great at English.
    """
    model = _get_model()

    if language == "hi":
        beam_size = 5
        initial_prompt = "नमस्ते, यह हिंदी में एक स्पष्ट बातचीत है।"
    else:
        beam_size = 1
        initial_prompt = None

    segments, info = model.transcribe(
        io.BytesIO(audio_bytes),  # wrap bytes as a file-like object
        language=language,        # None = auto-detect; "en"/"hi" = force it
        beam_size=beam_size,
        initial_prompt=initial_prompt,
        vad_filter=True,          # skip silence -> faster + cleaner transcript
    )
    text = "".join(seg.text for seg in segments).strip()
    return text, (language or info.language)

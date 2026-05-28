"""
All tunable settings in one place.
os.getenv("NAME", default) reads an environment variable if set, else uses
the default — exactly like process.env.NAME || default in Node.
"""
import os

# ---- ASR (speech -> text) ----
# Whisper model size. "medium" gives a big jump in Hindi accuracy over "small".
# It's ~1.5 GB but fits comfortably on the A30 alongside vLLM.
# "int8" = run in lower precision = much faster, marginal accuracy loss.
ASR_MODEL = os.getenv("ASR_MODEL", "medium")
ASR_DEVICE = os.getenv("ASR_DEVICE", "cuda")        # "cuda" = GPU, "cpu" = laptop
ASR_COMPUTE = os.getenv("ASR_COMPUTE", "int8")

# ---- LLM (the brain) ----
# We call vLLM, which speaks the OpenAI API. This is the address of that server.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8001/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")  # vLLM ignores it, but the client requires a value
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "200"))  # keep replies short = lower latency
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.4"))

# ---- TTS (text -> speech) ----
# Kokoro voices, chosen per language. English uses an American-English voice;
# Hindi uses a Hindi voice. Kokoro lang codes: "a" = US English, "h" = Hindi.
TTS_VOICE_EN = os.getenv("TTS_VOICE_EN", "af_heart")
TTS_VOICE_HI = os.getenv("TTS_VOICE_HI", "hf_alpha")
TTS_SAMPLE_RATE = 24000                          # Kokoro outputs 24kHz audio

# ---- Assistant persona / behavior ----
KNOWLEDGE_FILE = os.getenv("KNOWLEDGE_FILE", "knowledge.json")

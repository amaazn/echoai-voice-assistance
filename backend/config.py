"""
All tunable settings in one place.
os.getenv("NAME", default) reads an environment variable if set, else uses
the default — exactly like process.env.NAME || default in Node.
"""
import os

# ---- ASR (speech -> text) ----
# Whisper model size. "base" is fast and fine for a demo; "small"/"medium"
# are more accurate but slower. "int8" = run in lower precision = faster.
ASR_MODEL = os.getenv("ASR_MODEL", "base")
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
TTS_VOICE = os.getenv("TTS_VOICE", "af_heart")  # a Kokoro voice preset
TTS_SAMPLE_RATE = 24000                          # Kokoro outputs 24kHz audio

# ---- Where the grounding facts live ----
KNOWLEDGE_FILE = os.getenv("KNOWLEDGE_FILE", "knowledge.json")

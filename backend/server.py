"""
The web server (our "Express app").

Route /talk:
  receive audio  ->  ASR (speech->text)  ->  LLM (reply)  ->  TTS (speech)
  ->  return { transcript, reply, audio(base64), timings }

Run it with:  uvicorn server:app --host 0.0.0.0 --port 8000
"""
import base64
import time

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

import asr
import llm
import tts

app = FastAPI(title="Voice Assistant")

# CORS = lets the browser (a different origin, e.g. localhost:5173) call this API.
# Same idea as the `cors` middleware you add in Express.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # demo-friendly; tighten to your frontend URL for prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory conversation history (single user / single session demo).
# For multiple users you'd key this by a session id; fine for this assessment.
conversation: list[dict] = []


@app.get("/health")
def health():
    """Quick check that the server is up (open this in a browser)."""
    return {"status": "ok"}


@app.post("/reset")
def reset():
    """Clear the conversation so you can start a fresh chat."""
    conversation.clear()
    return {"status": "cleared"}


@app.post("/talk")
async def talk(audio: UploadFile = File(...), language: str = Form("en")):
    timings = {}
    audio_bytes = await audio.read()

    # 1) Speech -> text. `language` comes from the EN/HI toggle in the UI, so we
    # force Whisper to it (reliable) instead of letting it guess.
    t0 = time.time()
    transcript, lang = asr.transcribe(audio_bytes, language=language)
    timings["asr_ms"] = round((time.time() - t0) * 1000)

    if not transcript:
        return {"transcript": "", "reply": "Sorry, I didn't catch that.", "audio": "", "timings": timings}

    # 2) Text -> reply (add user turn, ask the LLM, store its answer)
    conversation.append({"role": "user", "content": transcript})
    t0 = time.time()
    reply = llm.generate(conversation)
    timings["llm_ms"] = round((time.time() - t0) * 1000)
    conversation.append({"role": "assistant", "content": reply})

    # 3) Reply text -> speech (voice matches the detected language), then base64
    t0 = time.time()
    wav_bytes = tts.synthesize(reply, lang=lang)
    timings["tts_ms"] = round((time.time() - t0) * 1000)
    audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")

    timings["total_ms"] = timings["asr_ms"] + timings["llm_ms"] + timings["tts_ms"]

    return {
        "transcript": transcript,
        "reply": reply,
        "language": lang,
        "audio": audio_b64,
        "timings": timings,
    }

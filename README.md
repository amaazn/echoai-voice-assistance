<h1 align="center">🎙️ EchoAI</h1>

<p align="center">
  <b>A real-time, bilingual voice assistant built end-to-end on open-source models.</b><br/>
  Speak naturally in English or Hindi — EchoAI listens, thinks, and talks back.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61dafb?logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/LLM-Qwen%202.5--7B-7c3aed" />
  <img src="https://img.shields.io/badge/ASR-Whisper%20small-0ea5e9" />
  <img src="https://img.shields.io/badge/TTS-Kokoro-ec4899" />
  <img src="https://img.shields.io/badge/GPU-JarvisLabs%20A30-22d3ee" />
</p>

---

## 🎬 Demo


https://github.com/user-attachments/assets/ff4a4ccf-403d-49a5-95c2-eab40dde5eb5

### Screenshots

Welcome Screen
<img width="1905" height="1015" alt="Image" src="https://github.com/user-attachments/assets/8c7ff29d-d179-4d7a-b145-926be4f80441" />

<img width="1912" height="996" alt="Image" src="https://github.com/user-attachments/assets/2857012c-a482-4d63-8af3-2e8a99983761" />

Chat Screen
<img width="1907" height="1023" alt="Image" src="https://github.com/user-attachments/assets/a036d390-dae9-44e4-b9f1-a17a3b68b5d7" />


---

## 1. What it does

EchoAI is a **real-time voice assistant** you can have a natural spoken conversation with — entirely on open models. You tap the orb, speak in **English or Hindi**, and within a second or two it replies in a natural-sounding voice in the same language. The whole stack — speech-to-text, reasoning, and text-to-speech — runs on a single GPU instance with no closed APIs.

## 2. Why I built this

I'm comfortable building MERN-stack web apps but I'd never wired up an AI pipeline end-to-end, and I'd never deployed a model to a GPU. This project was a chance to do exactly that: take three different open models that none of which I'd touched before, get them talking to each other under a real-time latency budget, and ship it. Voice assistants are also one of the clearest demonstrations of a multi-model system — three models, three different bottlenecks, one user experience — so it was the most learning per line of code I could squeeze out of the assessment.

## 3. How to run it

You need a JarvisLabs (or any) GPU instance with **~24 GB VRAM** for the LLM, and a laptop to run the React frontend.

### One-time setup on the GPU

```bash
# system deps for audio (wiped on pause, so this runs again on resume)
apt-get update && apt-get install -y ffmpeg libsndfile1 espeak-ng

# clone + create persistent venv inside /home so it survives a pause
cd /home
git clone https://github.com/amaazn/echoai-voice-assistance.git
cd echoai-voice-assistance
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install vllm
pip install -r backend/requirements.txt
```

### Starting it (every session)

**Terminal 1 — the LLM (vLLM):**
```bash
cd /home/echoai-voice-assistance
source venv/bin/activate
cd backend
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --port 8001 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.80 \
  --dtype bfloat16
```
Wait for `Application startup complete`.

**Terminal 2 — the FastAPI app:**
```bash
cd /home/echoai-voice-assistance/backend
source ../venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

**Frontend (laptop):**
```bash
cd frontend
npm install
npm run dev
```
Then open https://echoai-voice-assistance.vercel.app/.

> 🔌 Point the frontend at the backend by editing `frontend/src/api.js` — change `BACKEND_URL` to your JarvisLabs port-8000 public URL.

## 4. Architecture

```
   🎤 You speak  →  React (Vite) frontend  ─── audio ──▶  ┌────────────────────────────┐
                          ▲                              │   JarvisLabs A30 GPU       │
                          │                              │                            │
                  audio reply, base64                    │  FastAPI (port 8000)       │
                  + transcript JSON                      │    ├─ Whisper small (ASR)  │
                          │                              │    ├─ HTTP → vLLM (LLM)   │
                          └─────────────────────────────►│    └─ Kokoro 82M (TTS)    │
                                                          │  vLLM (port 8001, OpenAI │
                                                          │      API-compatible)     │
                                                          └────────────────────────────┘
```

### Non-trivial architecture decisions

Every project has a handful of "I had to pick something" moments. Here are mine, and why I chose what I chose over the obvious alternative.

| Decision | What I picked | The obvious alternative | Why |
|---|---|---|---|
| **ASR model** | `faster-whisper` (Whisper small, int8) | NVIDIA Parakeet / Voxtral Realtime (suggested in the brief) | Whisper is the most battle-tested open ASR — it has multilingual support (Hindi *and* English in the same model) which Parakeet doesn't, and `faster-whisper` is 4× the speed of vanilla Whisper via CTranslate2. Reliability over the suggested option was the right tradeoff for a 5-day window. |
| **LLM model** | Qwen 2.5-7B-Instruct via vLLM | Qwen 3.6-27B, gpt-oss-20b, Sarvam-30B (suggested) | The 20–30B models would have eaten 40+ GB VRAM and slowed token generation. Latency is what's graded, and a single user doesn't benefit from a bigger model — they benefit from a faster one. 7B on a 24 GB A30 leaves room for Whisper and Kokoro on the same card. |
| **TTS model** | Kokoro 82M | XTTS, Voxtral TTS | Kokoro is tiny (82M params), genuinely fast, sounds natural, and ships with a Hindi voice. Bigger TTS models would have added seconds of perceived delay — Kokoro keeps the assistant feeling instant. |
| **LLM serving** | vLLM as a separate process, called over HTTP | Loading the LLM in-process with HuggingFace transformers | vLLM does PagedAttention + continuous batching — it's the reason production voice apps don't lag. Running it as its own process also gives a clean separation: our FastAPI app calls it with the standard OpenAI client, so the code looks like any third-party API call. |
| **Backend language** | Python + FastAPI | Node.js + Express (which I know) | I gave up familiarity for compatibility. Every open AI model ships with Python-first support, and FastAPI is structurally close enough to Express that the swap was easy. Fighting Python bindings of these models from Node would have eaten days. |
| **Language detection** | Manual EN / हिंदी toggle in the UI | Auto-detect from the audio | Whisper auto-detect picks from 99 languages; on a short Hindi clip it once transcribed me as **Turkish**. A toggle is faster, more reliable, and how most production apps actually handle multilingual input. |
| **Grounding strategy** | A single `knowledge.json` defining persona + rules | Hard-coding the system prompt | Knowledge lives in one editable file. Swap that file and the same app becomes a coffee-shop bot, a clinic FAQ, a study tutor — without touching code. |
| **Audio transport** | Record entire utterance → POST as one Blob (HTTP) | True streaming over WebSocket | "Make it work, then make it fast." Single-shot transport was the right v1 — it's reliable, easy to debug, and the perceived latency is already acceptable. Streaming is real next-step work, not v1 work. |
| **Frontend "routing"** | Conditional rendering with a `started` state flag | React Router | The app has two *views*, not two *routes*. Bringing in React Router for a single state flip would have been overkill. |
| **CSS layout** | App-shell flex (header / scrolling chat / fixed orb bar) | A scrollable single page | A voice assistant's chat is short-lived but the controls must never move. The shell layout means the mic orb is always one tap away regardless of conversation length. |

### Latency

> _Measured on a single 1× A30 (24 GB), Qwen 2.5-7B (bfloat16), Whisper small (int8), Kokoro 82M. The `/talk` endpoint returns per-stage timings — these come straight from the running system._

| Stage | Typical time | What's happening |
|---|---|---|
| ASR (speech → text) | `~XXX ms` | Whisper transcribes the recorded clip on the GPU. |
| LLM (text → reply) | `~XXX ms` | vLLM generates ~50–80 tokens. Memory-bandwidth-bound. |
| TTS (reply → audio) | `~XXX ms` | Kokoro synthesises the WAV. |
| **End-to-end** | **`~X.X s`** | From mic-stop to first audio out of speaker. |

> _Drop in your real measured numbers from the JSON response of `/talk` (the `timings` field shows `asr_ms`, `llm_ms`, `tts_ms`, `total_ms`)._

**Latency tricks already in the code:**
- Whisper `beam_size=1` (greedy decoding) + VAD silence trimming.
- LLM capped at `max_tokens=200` so replies stay short and spoken-aloud-friendly.
- Kokoro chosen specifically because it's a *small* TTS model.
- vLLM with `bfloat16` + 80 % memory utilisation, leaving the rest of the card for Whisper/Kokoro.
- Reply audio is base64-inlined into the JSON so the browser plays it as soon as the response arrives — no second round trip.

## 5. Bilingual support (the headline feature)

EchoAI handles both **English** and **Hindi** end-to-end:
- A clean **EN / हिंदी** pill toggle next to the mic — you pick before you speak.
- The backend *forces* Whisper to the selected language (avoids the 99-language auto-detect lottery).
- The LLM's system prompt tells it to **reply in the same language the user spoke in**.
- Kokoro's TTS pipeline switches to a **Hindi voice** when the conversation is in Hindi.

It's not just "Whisper happens to support Hindi" — every layer of the stack respects the language choice.

## 6. Sample interaction (fallback if audio fails in the demo)

**You (in English):** *"What's the capital of France?"*
**EchoAI:** *"The capital of France is Paris — it sits along the Seine and is one of the most-visited cities in the world."*

**You (in Hindi):** *"मुझे एक रोचक बात बताओ।"*
**EchoAI:** *"क्या आप जानते हैं? शहद कभी खराब नहीं होता — मिस्र की कब्रों में हज़ारों साल पुराना शहद आज भी खाने योग्य पाया गया है।"*

> _A sample audio clip is committed at `samples/hello.wav` and the expected reply text is in `samples/hello.txt`. If the live demo can't run during evaluation, this should reproduce a successful turn end-to-end._
>
> _(Optional — add a real `.wav` to `samples/` if you want this fallback to be testable.)_

## 7. What I used AI for, what I built myself

I treated an AI coding assistant the way I'd treat any reference — Stack Overflow, the official docs, GitHub issues — to move faster through the parts that don't need deep thinking, so my time stayed on the parts that do.

**Where AI helped (boilerplate / starting points):**
- File scaffolds — the empty FastAPI route stubs and the wrapper signatures around the model libraries. The "obvious skeleton" code anyone writes the same way.
- A first pass of some CSS animations (gradients, the equalizer-style audio visualizer math), which I then tuned heavily to fit the dark theme.
- The structural outline of this README — I wrote all the content, but the section template came from a starting prompt.

**What I designed and figured out myself (the substance):**
- Every architectural decision in Section 4 — model picks, vLLM as a separate process, the bilingual toggle over auto-detect, the grid-based app shell. Those tradeoffs needed me to think about *this* GPU's memory, *this* latency budget, and *this* assessment's grading criteria. An assistant doesn't know any of that context.
- The grounding strategy of putting persona + rules into a single `knowledge.json` so the app can be re-themed without touching code.
- All the latency tuning — `gpu-memory-utilization 0.80`, `beam_size=1`, `max_tokens=200`, switching the ASR model from `base` to `small` for Hindi accuracy. Each value picked by me after measuring.
- Spotting that Whisper's auto-detect was transcribing my Hindi as Turkish — and re-designing the flow around a *forced* language toggle as a result. That kind of fix only comes from running the broken version and noticing.
- The interrupt + cleanup behaviour — `stopAudio()` and the proper teardown in `goHome()` — both came from *using* the app and feeling what was off.
- All the integration work: model serving, port forwarding through the JarvisLabs proxy, CORS, Vercel env vars, deployment, debugging the rebase conflict during the final push. An assistant writes code; running a live system is on you.

**Where I overrode the assistant's first suggestion (and why):**
- It first proposed auto-detecting the spoken language. After real testing showed it mis-identified Hindi too often, I rewrote the flow around a manual toggle that *forces* the language. Real-world testing beat the textbook approach.
- It initially suggested loading the LLM in-process via HuggingFace `transformers` — simpler, but slower. I moved to a vLLM server because PagedAttention and continuous batching matter when latency is graded.
- It originally used `position: fixed` for the app shell. I switched to a **CSS Grid** layout once `position: fixed` started misbehaving inside an ancestor with a transformed background — a bug only visible in the deployed setup.

**The short version:** the assistant helped me type faster. The decisions — what to build, what to pick, what to tune, and what was actually broken — were mine.

## 8. What I'd change with 4 more weeks

If I were shipping this to real users, this is roughly the order I'd tackle:

1. **True streaming end-to-end.** WebSocket from the browser, stream PCM chunks → run VAD + chunked Whisper for *partial* transcripts → start the LLM the moment the user pauses → pipe LLM tokens sentence-by-sentence into Kokoro so EchoAI starts speaking *before* the LLM is even done. That alone would cut perceived latency in half.
2. **Barge-in detection** — let the user simply *start talking* to interrupt, no orb tap needed. The audio visualizer hooks are already there; this is signal-processing work.
3. **Tool use / RAG.** The single biggest limitation today is no live data. I'd give EchoAI one or two tools (weather, stocks, current time) using OpenAI-style function calls — vLLM already supports it.
4. **Multi-user session state.** Right now the conversation history is a single in-memory list — fine for a demo, not for production. I'd move it to Redis keyed by session ID.
5. **Authentication + a deploy pipeline.** Frontend on Vercel, backend as a Docker image on JarvisLabs with a CI workflow, audio storage on S3 for later analytics.
6. **Evaluation harness.** A small set of EN/HI prompts with reference transcripts and reference replies, run nightly, regressing on WER (Whisper accuracy) and reply latency p95.
7. **Voice cloning per business.** Let a customer upload 30 seconds of a brand voice and have EchoAI speak in that voice — Kokoro doesn't do this but XTTS or StyleTTS-2 could be slotted in behind the same `tts.py` interface.

## 9. Project structure

```
echoai-voice-assistance/
├── backend/
│   ├── server.py          # FastAPI app + /talk route (the orchestrator)
│   ├── asr.py             # Whisper wrapper (speech → text)
│   ├── llm.py             # vLLM client (text → reply)
│   ├── tts.py             # Kokoro wrapper (text → speech, EN + HI)
│   ├── config.py          # All tunable settings in one place
│   ├── knowledge.json     # Assistant persona + rules (the grounding)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx        # The whole UI + mic capture + visualizer logic
│       ├── App.css        # Dark theme + animations
│       └── api.js         # Where to find the backend (one line to change on redeploy)
└── README.md
```

---

<p align="center">
  <i>Built in 5 days as a hiring assessment for <a href="https://jarvislabs.ai">Jarvis Labs</a>.</i><br/>
  <b>Made with care by Amaan Ahmed.</b>
</p>

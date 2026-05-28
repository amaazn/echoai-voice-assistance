import { useState, useRef, useEffect } from "react";
import { BACKEND_URL } from "./api";
import "./App.css";

const BAR_COUNT = 32; // number of bars in the live audio visualizer

export default function App() {
  // --- UI state ---
  const [started, setStarted] = useState(false); // false = show welcome screen
  const [phase, setPhase] = useState("idle"); // idle | listening | thinking | speaking
  const [turns, setTurns] = useState([]); // conversation: {role, text}
  const [error, setError] = useState("");
  const [lang, setLang] = useState("en"); // "en" or "hi" — which language you'll speak
  const [lastTimings, setLastTimings] = useState(null); // { asr_ms, llm_ms, tts_ms, total_ms, wall_ms }

  // --- machinery that doesn't need to trigger re-renders ---
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const rafRef = useRef(null);
  const barsRef = useRef([]); // DOM nodes for the visualizer bars
  const transcriptEndRef = useRef(null);
  const currentAudioRef = useRef(null); // the reply audio currently playing

  // auto-scroll the conversation to the newest message
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  // ---------- LIVE AUDIO VISUALIZER ----------
  // Reads the mic's frequency data ~60x/sec and writes bar heights straight
  // to the DOM (via refs) so we get a smooth equalizer without re-rendering.
  function startVisualizer(stream) {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);
    audioCtxRef.current = ctx;
    analyserRef.current = analyser;

    const data = new Uint8Array(analyser.frequencyBinCount);
    const loop = () => {
      analyser.getByteFrequencyData(data);
      for (let i = 0; i < BAR_COUNT; i++) {
        const v = data[i % data.length] / 255; // 0..1
        const bar = barsRef.current[i];
        if (bar) bar.style.transform = `scaleY(${0.08 + v * 0.92})`;
      }
      rafRef.current = requestAnimationFrame(loop);
    };
    loop();
  }

  function stopVisualizer() {
    cancelAnimationFrame(rafRef.current);
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
    barsRef.current.forEach((b) => b && (b.style.transform = "scaleY(0.08)"));
  }

  // Stop any reply that's currently playing (used to interrupt EchoAI).
  function stopAudio() {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.onended = null;
      currentAudioRef.current = null;
    }
  }

  // ---------- RECORDING ----------
  async function startRecording() {
    setError("");
    stopAudio(); // if EchoAI is mid-sentence, cut it off so we can listen now
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data);
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        stopVisualizer();
        sendToBackend(blob);
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setPhase("listening");
      startVisualizer(stream);
    } catch (err) {
      setError("Microphone access denied: " + err.message);
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
  }

  // Go back to the welcome screen, cleanly shutting everything down so
  // nothing keeps recording or playing in the background.
  function goHome() {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state === "recording") {
      mr.onstop = null; // detach so it doesn't fire a request on the way out
      mr.stop();
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    stopVisualizer();
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    setPhase("idle");
    setStarted(false);
  }

  // ---------- SEND TO BACKEND ----------
  async function sendToBackend(blob) {
    setPhase("thinking");
    try {
      const form = new FormData();
      form.append("audio", blob, "speech.webm");
      form.append("language", lang); // tell the backend which language to expect
      const t0 = performance.now(); // wall-clock: client perspective
      const res = await fetch(`${BACKEND_URL}/talk`, { method: "POST", body: form });
      if (!res.ok) throw new Error("Server error " + res.status);
      const data = await res.json();
      const wall_ms = Math.round(performance.now() - t0);

      // Capture timings for the latency badge
      if (data.timings) {
        setLastTimings({ ...data.timings, wall_ms });
      }

      setTurns((prev) => [
        ...prev,
        { role: "user", text: data.transcript || "…" },
        { role: "assistant", text: data.reply },
      ]);

      if (data.audio) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
        currentAudioRef.current = audio;
        setPhase("speaking");
        audio.onended = () => setPhase("idle");
        audio.play().catch(() => setPhase("idle"));
      } else {
        setPhase("idle");
      }
    } catch (err) {
      setError("Couldn't reach the assistant: " + err.message);
      setPhase("idle");
    }
  }

  const isListening = phase === "listening";
  const orbClick = isListening ? stopRecording : startRecording;
  const orbDisabled = phase === "thinking"; // can interrupt while speaking, only wait while thinking

  const phaseLabel = {
    idle: "Tap the orb and start speaking",
    listening: "Listening… tap STOP when you're done",
    thinking: "Thinking…",
    speaking: "Speaking… (tap the orb to interrupt)",
  }[phase];

  // ---------- WELCOME SCREEN ----------
  if (!started) {
    return (
      <div className="stage welcome">
        <div className="aurora" />
        <div className="welcome-card">
          <div className="logo-orb">
            <span>◎</span>
          </div>
          <h1 className="title">
            <span className="grad">EchoAI</span>
          </h1>
          <p className="subtitle">
            Your real-time voice assistant. Speak naturally — EchoAI listens,
            thinks, and talks back.
          </p>
          <div className="pills">
            <span className="pill">🎤 Speech&nbsp;→&nbsp;Text</span>
            <span className="pill">🧠 Reasoning</span>
            <span className="pill">🔊 Natural Voice</span>
          </div>
          <button className="cta" onClick={() => setStarted(true)}>
            Start talking →
          </button>
          <p className="hint">Powered by open models · Whisper · Qwen · Kokoro</p>
          <p className="credit">Made by Amaan</p>
        </div>
      </div>
    );
  }

  // ---------- MAIN APP ----------
  return (
    <div className="stage">
      <div className="aurora" />

      <header className="topbar">
        <button className="back-btn" onClick={goHome} aria-label="Back to home">
          ←
        </button>
        <div className="brand">
          <span className="brand-dot" /> EchoAI
        </div>
        <span className={`status-chip ${phase}`}>{phaseLabel}</span>
      </header>

      <main className="conversation">
        {turns.length === 0 ? (
          <div className="empty">
            <p>Say hello 👋</p>
            <p className="empty-sub">Speak in English or Hindi — ask me anything</p>
          </div>
        ) : (
          <div className="messages">
            {turns.map((t, i) => (
              <div key={i} className={`bubble ${t.role}`}>
                <div className="who">{t.role === "user" ? "You" : "EchoAI"}</div>
                <div className="text">{t.text}</div>
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>
        )}
      </main>

      {lastTimings && (
        <div className="latency-badge" title="Per-stage backend latency (server compute only)">
          <span className="latency-label">Latency</span>
          <span className="latency-main">
            ⚡ {(lastTimings.total_ms / 1000).toFixed(2)}s
            <span className="latency-detail">
              &nbsp;· ASR {lastTimings.asr_ms}ms · LLM {lastTimings.llm_ms}ms · TTS {lastTimings.tts_ms}ms
              &nbsp;· wall {(lastTimings.wall_ms / 1000).toFixed(2)}s
            </span>
          </span>
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <footer className="controls">
        <div className="lang-toggle">
          <button
            className={lang === "en" ? "active" : ""}
            onClick={() => setLang("en")}
          >
            EN
          </button>
          <button
            className={lang === "hi" ? "active" : ""}
            onClick={() => setLang("hi")}
          >
            हिंदी
          </button>
        </div>

        <div className={`orb-wrap ${phase}`}>
          {/* live audio bars (only animate while listening) */}
          <div className={`visualizer ${isListening ? "on" : ""}`}>
            {Array.from({ length: BAR_COUNT }).map((_, i) => (
              <span key={i} ref={(el) => (barsRef.current[i] = el)} className="bar" />
            ))}
          </div>

          <button
            className={`orb ${phase}`}
            onClick={orbClick}
            disabled={orbDisabled}
            aria-label="microphone"
          >
            <span className={`orb-icon ${isListening ? "stop" : ""}`}>
              {phase === "thinking" ? "•••" : isListening ? "STOP" : "🎤"}
            </span>
            {isListening && <span className="rec-dot" aria-hidden="true" />}
          </button>
        </div>
        <p className="controls-hint">{phaseLabel}</p>
      </footer>
    </div>
  );
}

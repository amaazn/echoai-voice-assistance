"""
LLM = the "brain" (text in -> reply text out).

We don't load the model here. Instead we call vLLM, a separate server that
runs the model and speaks the OpenAI API format. So this file looks just like
code that calls ChatGPT — but the requests go to our own model.
"""
import json
from openai import OpenAI
import config

# Create the client once. base_url points at our vLLM server, not OpenAI's.
_client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)


def _build_system_prompt() -> str:
    """Turn knowledge.json into the hidden instructions that shape the assistant."""
    with open(config.KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        kb = json.load(f)

    rules = "\n".join(f"- {rule}" for rule in kb["rules"])

    return (
        f"You are {kb['assistant_name']}, a real-time voice assistant.\n"
        f"{kb['description']}\n\n"
        f"Tone: {kb['tone']}\n\n"
        f"Rules you must follow:\n{rules}"
    )


# Build the system prompt once at import time.
SYSTEM_PROMPT = _build_system_prompt()


def generate(history: list[dict]) -> str:
    """
    history is a list of {"role": "user"/"assistant", "content": "..."} messages,
    the standard OpenAI chat format. We prepend the system prompt and ask for a reply.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    resp = _client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        max_tokens=config.LLM_MAX_TOKENS,
        temperature=config.LLM_TEMPERATURE,
    )
    return resp.choices[0].message.content.strip()

import json
from typing import Any

from ollama import Client

# Talks to the local Ollama server (http://localhost:11434, or OLLAMA_HOST).
MODEL = "qwen3.5:9b"


def ask(prompt: str, schema: dict[str, Any], max_tokens: int = 300) -> dict[str, Any]:
    """One-shot completion whose response is constrained to the JSON schema, returned parsed."""
    response = Client().chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        format=schema,
        # Reasoning would eat the token budget of these short answers.
        think=False,
        options={"num_predict": max_tokens},
    )
    return json.loads(response.message.content or "")

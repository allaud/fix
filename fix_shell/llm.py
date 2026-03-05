import json
import os
import subprocess
from urllib.request import Request, urlopen


def call_groq(prompt: str, system: str = "", model: str = "llama-3.3-70b-versatile") -> str:
    """Call Groq API directly via urllib (no deps needed)."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 256,
    }).encode()

    req = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "fix-shell/0.1",
        },
    )

    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    return data["choices"][0]["message"]["content"].strip()


def call_claude(prompt: str, system: str = "", model: str = "haiku") -> str:
    """Call claude CLI with -p (print mode)."""
    cmd = [
        "claude", "-p",
        "--model", model,
        "--no-session-persistence",
        "--tools", "",
    ]
    if system:
        cmd.extend(["--system-prompt", system])
    cmd.append(prompt)

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")

    return result.stdout.strip()

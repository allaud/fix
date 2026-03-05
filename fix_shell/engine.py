import os
import platform
import subprocess
import time

from .llm import call_claude, call_groq


CORRECTION_SYSTEM = """You are a shell command auto-corrector. The user ran a command that failed.
Given the failed command and its stderr output, respond with ONLY the corrected command.
No explanation, no markdown, no backticks — just the raw command.
If you cannot determine a fix, respond with exactly: UNKNOWN"""

NL_SYSTEM = """You are a shell command translator. Convert natural language to shell commands.
Context:
- OS: {os}
- Shell: {shell}
- Current directory: {cwd}

Respond with ONLY the shell command. No explanation, no markdown, no backticks — just the raw command.
If the request is ambiguous, pick the most common/safe interpretation.
If you truly cannot translate, respond with exactly: UNKNOWN"""


def _call(provider: str, model: str, prompt: str, system: str) -> str:
    if provider == "groq":
        return call_groq(prompt, system=system, model=model)
    else:
        return call_claude(prompt, system=system, model=model)


def correct_command(config: dict, failed_cmd: str, stderr: str) -> tuple[str | None, str, int]:
    """Correct a failed command. Returns (corrected_command, provider_used, elapsed_ms)."""
    section = config["correction"]
    provider = section.get("provider", "groq")
    model = section["model"]

    user_msg = f"Failed command: {failed_cmd}"
    if stderr:
        user_msg += f"\nStderr:\n{stderr}"

    used = provider
    t0 = time.monotonic()
    try:
        result = _call(provider, model, user_msg, CORRECTION_SYSTEM)
    except Exception as primary_err:
        print(f"\033[2m{provider} error: {primary_err}\033[0m")
        used = "claude_code" if provider == "groq" else "groq"
        fallback_model = "haiku" if used == "claude_code" else "llama-3.3-70b-versatile"
        try:
            result = _call(used, fallback_model, user_msg, CORRECTION_SYSTEM)
        except Exception as e:
            elapsed = int((time.monotonic() - t0) * 1000)
            print(f"\033[31mLLM error: {e}\033[0m")
            return None, "error", elapsed
    elapsed = int((time.monotonic() - t0) * 1000)

    if result == "UNKNOWN" or not result:
        return None, used, elapsed

    result = result.strip("`").strip()
    if "\n" in result:
        result = result.split("\n")[0]

    return result, used, elapsed


def translate_natural_language(config: dict, query: str) -> tuple[str | None, str, int]:
    """Translate natural language to a shell command. Returns (command, provider_used, elapsed_ms)."""
    section = config["natural_language"]
    provider = section.get("provider", "claude_code")
    model = section["model"]

    system = NL_SYSTEM.format(
        os=platform.system(),
        shell=os.environ.get("SHELL", "zsh"),
        cwd=os.getcwd(),
    )

    used = provider
    t0 = time.monotonic()
    try:
        result = _call(provider, model, query, system)
    except Exception as e:
        elapsed = int((time.monotonic() - t0) * 1000)
        print(f"\033[31mLLM error: {e}\033[0m")
        return None, used, elapsed
    elapsed = int((time.monotonic() - t0) * 1000)

    if result == "UNKNOWN" or not result:
        return None, used, elapsed

    result = result.strip("`").strip()
    if "\n" in result:
        result = result.split("\n")[0]

    return result, used, elapsed


def run_command(cmd: str) -> tuple[int, str]:
    """Run a shell command with stdout on the real TTY, capture only stderr."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            executable=os.environ.get("SHELL", "/bin/zsh"),
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode, result.stderr
    except Exception as e:
        return 1, str(e)

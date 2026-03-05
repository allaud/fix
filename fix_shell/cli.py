import argparse
import os
import sys

from .config import ensure_config, load_config
from .engine import translate_natural_language, correct_command
from .spinner import Spinner
from .countdown import countdown_and_run
from .shell import launch_fix_shell


def parse_args():
    parser = argparse.ArgumentParser(
        prog="fix",
        description="Terminal tool that auto-corrects commands and understands natural language",
    )
    parser.add_argument("--provider", "-p", choices=["groq", "claude_code"],
                        help="LLM provider for both correction and NL")
    parser.add_argument("--model", "-m",
                        help="Model for both correction and NL")
    parser.add_argument("--timeout", "-t", type=int,
                        help="Auto-approve timeout (seconds) for both")
    parser.add_argument("--groq-key", help="Groq API key (or set GROQ_API_KEY env var)")
    parser.add_argument("--icon", "-i", help="Prompt icon (e.g. ✦ ✨ ⚡ 🔮 λ)")
    parser.add_argument("--correct", nargs=argparse.REMAINDER,
                        help=argparse.SUPPRESS)  # internal
    parser.add_argument("query", nargs="*", help="Natural language query (one-shot mode)")
    return parser.parse_args()


PROVIDER_DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "claude_code": "sonnet",
}


def apply_overrides(config: dict, args) -> dict:
    """Apply CLI flags to both correction and natural_language sections."""
    for section in ("correction", "natural_language"):
        if args.provider:
            config[section]["provider"] = args.provider
            # If provider changed but no explicit model, use the provider's default
            if not args.model:
                config[section]["model"] = PROVIDER_DEFAULT_MODELS.get(args.provider, config[section]["model"])
        if args.model:
            config[section]["model"] = args.model
        if args.timeout is not None:
            config[section]["timeout"] = args.timeout
    return config


def main():
    ensure_config()
    args = parse_args()
    config = load_config()

    if args.groq_key:
        os.environ["GROQ_API_KEY"] = args.groq_key
    if args.icon:
        config["icon"] = args.icon

    if args.correct is not None:
        # Internal: called by zsh hook after a failed command
        # --correct <exit_code> <failed_cmd> [stderr...]
        parts = args.correct
        if len(parts) < 2:
            sys.exit(1)
        failed_cmd = parts[1]
        stderr = " ".join(parts[2:]) if len(parts) > 2 else ""
        config = apply_overrides(config, args)
        with Spinner("thinking..."):
            fix, provider, ms = correct_command(config, failed_cmd, stderr)
        if fix and fix != failed_cmd:
            print(f"\033[2m(via {provider}, {ms}ms)\033[0m \033[1;33m-> {fix}\033[0m")
            countdown_and_run(fix, seconds=int(config["correction"]["timeout"]))
        sys.exit(0)

    if not args.query:
        # Enter fix mode
        config = apply_overrides(config, args)
        launch_fix_shell(config)
        return

    # One-shot mode: natural language -> command
    query = " ".join(args.query)
    config = apply_overrides(config, args)
    with Spinner("thinking..."):
        cmd, provider, ms = translate_natural_language(config, query)
    if cmd:
        print(f"\033[2m(via {provider}, {ms}ms)\033[0m \033[1;33m-> {cmd}\033[0m")
        countdown_and_run(cmd, seconds=int(config["natural_language"]["timeout"]))
    else:
        print("\033[31mCouldn't translate that to a command.\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    main()

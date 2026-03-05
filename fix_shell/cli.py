import argparse
import os
import sys

from .config import load_config
from .engine import translate_natural_language, correct_command
from .spinner import Spinner
from .countdown import countdown_and_run
from .shell import launch_fix_shell


PROVIDER_DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "claude_code": "sonnet",
}


def parse_args():
    parser = argparse.ArgumentParser(
        prog="fix",
        description="Terminal tool that auto-corrects commands and understands natural language",
    )
    parser.add_argument("--provider", "-p", choices=["groq", "claude_code"],
                        help="LLM provider for both AC and NL")
    parser.add_argument("--ac-provider", choices=["groq", "claude_code"],
                        help="Auto-correction provider")
    parser.add_argument("--ac-model", help="Auto-correction model")
    parser.add_argument("--ac-timeout", type=int, help="Auto-correction timeout (seconds)")
    parser.add_argument("--nl-provider", choices=["groq", "claude_code"],
                        help="Natural language provider")
    parser.add_argument("--nl-model", help="Natural language model")
    parser.add_argument("--nl-timeout", type=int, help="Natural language timeout (seconds)")
    parser.add_argument("--model", "-m", help="Model for both AC and NL")
    parser.add_argument("--timeout", "-t", type=int, help="Timeout for both AC and NL")
    parser.add_argument("--groq-key", help="Groq API key")
    parser.add_argument("--icon", "-i", help="Prompt icon")
    parser.add_argument("--correct", nargs=argparse.REMAINDER,
                        help=argparse.SUPPRESS)
    parser.add_argument("query", nargs="*", help="Natural language query (one-shot mode)")
    return parser.parse_args()


def apply_overrides(config: dict, args) -> dict:
    if args.groq_key:
        config["groq_api_key"] = args.groq_key
        os.environ["GROQ_API_KEY"] = args.groq_key
    if args.icon:
        config["icon"] = args.icon
    if args.provider:
        config["ac_provider"] = args.provider
        config["nl_provider"] = args.provider
        if not args.model and not args.ac_model:
            config["ac_model"] = PROVIDER_DEFAULT_MODELS.get(args.provider, config["ac_model"])
        if not args.model and not args.nl_model:
            config["nl_model"] = PROVIDER_DEFAULT_MODELS.get(args.provider, config["nl_model"])
    if args.model:
        config["ac_model"] = args.model
        config["nl_model"] = args.model
    if args.timeout is not None:
        config["ac_timeout"] = str(args.timeout)
        config["nl_timeout"] = str(args.timeout)
    # Specific overrides win over --provider / --model / --timeout
    if args.ac_provider:
        config["ac_provider"] = args.ac_provider
        if not args.model and not args.ac_model:
            config["ac_model"] = PROVIDER_DEFAULT_MODELS.get(args.ac_provider, config["ac_model"])
    if args.ac_model:
        config["ac_model"] = args.ac_model
    if args.ac_timeout is not None:
        config["ac_timeout"] = str(args.ac_timeout)
    if args.nl_provider:
        config["nl_provider"] = args.nl_provider
        if not args.model and not args.nl_model:
            config["nl_model"] = PROVIDER_DEFAULT_MODELS.get(args.nl_provider, config["nl_model"])
    if args.nl_model:
        config["nl_model"] = args.nl_model
    if args.nl_timeout is not None:
        config["nl_timeout"] = str(args.nl_timeout)
    return config


def main():
    args = parse_args()
    config = load_config()
    config = apply_overrides(config, args)

    if args.correct is not None:
        parts = args.correct
        if len(parts) < 2:
            sys.exit(1)
        failed_cmd = parts[1]
        stderr = " ".join(parts[2:]) if len(parts) > 2 else ""
        with Spinner("thinking..."):
            fix, provider, model, ms = correct_command(config, failed_cmd, stderr)
        if fix and fix != failed_cmd:
            print(f"\033[1;33m-> {fix}\033[0m \033[2m(via {provider}, {model}, {ms}ms)\033[0m")
            countdown_and_run(fix, seconds=int(config["ac_timeout"]))
        sys.exit(0)

    if not args.query:
        launch_fix_shell(config)
        return

    query = " ".join(args.query)
    with Spinner("thinking..."):
        cmd, provider, model, ms = translate_natural_language(config, query)
    if cmd:
        print(f"\033[1;33m-> {cmd}\033[0m \033[2m(via {provider}, {model}, {ms}ms)\033[0m")
        countdown_and_run(cmd, seconds=int(config["nl_timeout"]))
    else:
        print("\033[31mCouldn't translate that to a command.\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    main()

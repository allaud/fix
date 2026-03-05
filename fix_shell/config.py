import os
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

CONFIG_PATH = os.path.expanduser("~/.config/fix/config.toml")

DEFAULT_CONFIG = {
    "icon": "\U0001f4ab",
    "correction": {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "timeout": 0,
    },
    "natural_language": {
        "provider": "claude_code",
        "model": "sonnet",
        "timeout": 3,
    },
}


def load_config() -> dict:
    config = _deep_copy(DEFAULT_CONFIG)

    if os.path.exists(CONFIG_PATH):
        if tomllib is None:
            print("Warning: install 'tomli' package to read config file on Python <3.11")
        else:
            with open(CONFIG_PATH, "rb") as f:
                user_config = tomllib.load(f)
            _deep_merge(config, user_config)

    return config


def ensure_config():
    """Create default config file if it doesn't exist."""
    config_dir = os.path.dirname(CONFIG_PATH)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            f.write("""# fix-shell configuration
icon = "💫"                           # prompt icon (e.g. "✨", "⚡", "🔮", "✦")

[correction]
provider = "groq"                    # "groq" or "claude_code"
model = "llama-3.3-70b-versatile"
timeout = 0                          # seconds before auto-run (0 = instant)

[natural_language]
provider = "claude_code"             # "groq" or "claude_code"
model = "sonnet"
timeout = 3                          # seconds before auto-run (0 = instant)
""")
        print(f"Created config at {CONFIG_PATH}")


def _deep_copy(d: dict) -> dict:
    return {k: _deep_copy(v) if isinstance(v, dict) else v for k, v in d.items()}


def _deep_merge(base: dict, override: dict):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v

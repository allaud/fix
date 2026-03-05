import os

DEFAULTS = {
    "icon": "💫",
    "ac_provider": "groq",
    "ac_model": "llama-3.3-70b-versatile",
    "ac_timeout": "0",
    "nl_provider": "claude_code",
    "nl_model": "sonnet",
    "nl_timeout": "3",
    "groq_api_key": "",
}

ENV_MAP = {
    "icon": "FIX_ICON",
    "ac_provider": "FIX_AC_PROVIDER",
    "ac_model": "FIX_AC_MODEL",
    "ac_timeout": "FIX_AC_TIMEOUT",
    "nl_provider": "FIX_NL_PROVIDER",
    "nl_model": "FIX_NL_MODEL",
    "nl_timeout": "FIX_NL_TIMEOUT",
    "groq_api_key": "GROQ_API_KEY",
}


def load_config() -> dict:
    config = {}
    for key, default in DEFAULTS.items():
        env_var = ENV_MAP[key]
        config[key] = os.environ.get(env_var, default)
    return config

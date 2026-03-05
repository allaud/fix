import os
import sys
import shutil
import subprocess
import tempfile


FIX_ZSHRC = """
# Preserve real history
export HISTFILE="$HOME/.zsh_history"

# Source user's real zsh config
if [[ -f "{user_zshrc}" ]]; then
    source "{user_zshrc}"
fi

# --- fix mode hooks ---

# Store the last command and its stderr
__fix_last_cmd=""
__fix_stderr_file=$(mktemp)

# preexec: capture the command before it runs
__fix_preexec() {{
    __fix_last_cmd="$1"
}}

# precmd: after each command, check if it failed
__fix_precmd() {{
    local exit_code=$?
    if [[ $exit_code -ne 0 && -n "$__fix_last_cmd" ]]; then
        local stderr_content=""
        if [[ -s "$__fix_stderr_file" ]]; then
            stderr_content=$(cat "$__fix_stderr_file")
        fi
        {fix_cmd} --correct "$exit_code" "$__fix_last_cmd" "$stderr_content"
    fi
    __fix_last_cmd=""
    : > "$__fix_stderr_file"
}}

# Wrap command execution to capture stderr
__fix_exec() {{
    exec 2> >(tee "$__fix_stderr_file" >&2)
}}

autoload -Uz add-zsh-hook
add-zsh-hook preexec __fix_preexec
add-zsh-hook precmd __fix_precmd

# Capture stderr
__fix_exec

# Prepend icon to prompt — runs last so it's after theme hooks
__fix_icon="{icon}"
__fix_patch_prompt() {{
    PROMPT="${{__fix_icon}} ${{PROMPT#${{__fix_icon}} }}"
}}
precmd_functions+=(__fix_patch_prompt)

# Cleanup on exit
__fix_cleanup() {{
    rm -f "$__fix_stderr_file"
}}
add-zsh-hook zshexit __fix_cleanup

# Natural language: ? <query>
__fix_nl() {{
    {fix_nl_cmd} "$*"
}}
alias '?'='noglob __fix_nl'
"""


def launch_fix_shell(config: dict):
    fix_bin = shutil.which("fix")
    if not fix_bin:
        # Use fix.py next to the package
        fix_py = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fix.py")
        fix_bin = f"{sys.executable} {fix_py}"

    groq_key = config["groq_api_key"]
    key_flag = f' --groq-key "{groq_key}"' if groq_key else ""

    fix_cmd = f'{fix_bin} --ac-provider {config["ac_provider"]} --ac-model {config["ac_model"]} --ac-timeout {config["ac_timeout"]}{key_flag}'

    fix_nl_cmd = f'{fix_bin} --nl-provider {config["nl_provider"]} --nl-model {config["nl_model"]} --nl-timeout {config["nl_timeout"]}{key_flag}'

    user_zshrc = os.path.expanduser("~/.zshrc")

    tmpdir = tempfile.mkdtemp(prefix="fix_shell_")
    tmp_zshrc = os.path.join(tmpdir, ".zshrc")

    icon = config["icon"]

    with open(tmp_zshrc, "w") as f:
        f.write(FIX_ZSHRC.format(
            user_zshrc=user_zshrc,
            fix_cmd=fix_cmd,
            fix_nl_cmd=fix_nl_cmd,
            icon=icon,
        ))

    env = os.environ.copy()
    env["ZDOTDIR"] = tmpdir
    env["FIX_MODE"] = "1"
    env.pop("CLAUDECODE", None)

    print("\033[2mfix mode \u2014 ? <query> for natural language, exit to leave\033[0m")
    print(f'\033[2m  autocorrect: {config["ac_provider"]}/{config["ac_model"]} (autoaccept: {config["ac_timeout"]}s)\033[0m')
    print(f'\033[2m  natural language: {config["nl_provider"]}/{config["nl_model"]} (autoaccept: {config["nl_timeout"]}s)\033[0m')

    try:
        result = subprocess.run(
            [os.environ.get("SHELL", "/bin/zsh")],
            env=env,
        )
        sys.exit(result.returncode)
    finally:
        try:
            os.unlink(tmp_zshrc)
            os.rmdir(tmpdir)
        except OSError:
            pass

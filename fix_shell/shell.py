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
        fix_bin = f"{sys.executable} -m fix_shell.cli"

    # Build flag string so inner fix calls use the same overrides
    cor = config["correction"]
    nl = config["natural_language"]

    groq_key = os.environ.get("GROQ_API_KEY", "")
    key_flag = f' --groq-key "{groq_key}"' if groq_key else ""

    flags = f"-p {cor.get('provider', 'groq')} -m {cor['model']} -t {cor['timeout']}{key_flag}"
    fix_cmd = f'"{fix_bin}" {flags}'

    # For NL calls, build separately (? uses NL settings)
    nl_flags = f"-p {nl.get('provider', 'claude_code')} -m {nl['model']} -t {nl['timeout']}{key_flag}"
    fix_nl_cmd = f'"{fix_bin}" {nl_flags}'

    user_zshrc = os.path.expanduser("~/.zshrc")

    tmpdir = tempfile.mkdtemp(prefix="fix_shell_")
    tmp_zshrc = os.path.join(tmpdir, ".zshrc")

    icon = config.get("icon", "\u2726")

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
    print(f"\033[2m  correction: {cor.get('provider', 'groq')}/{cor['model']} (timeout: {cor['timeout']}s)\033[0m")
    print(f"\033[2m  natural lang: {nl.get('provider', 'claude_code')}/{nl['model']} (timeout: {nl['timeout']}s)\033[0m")

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

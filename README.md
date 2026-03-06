# fix

- [How it works](#how-it-works)
- [Examples](#examples)
- [Installation](#installation)
- [Usage](#usage)

With modern development tools like Claude Code, the development cycle moves back to the terminal. But spinning up Claude Code for every small task feels heavy — what if there was a more seamless integration between your terminal and AI, without touching your color scheme, prompt, completions, or any other zsh settings?

**fix** does exactly that. It wraps your existing zsh in a thin AI layer:

- Typos and failed commands get auto-corrected instantly
- Natural language gets translated to shell commands
- Complex multi-step tasks run through full Claude Code sessions

Your terminal stays yours — fix just makes it smarter.

![demo](demo.gif)

## How it works

fix is a thin layer on top of your real zsh. It stays invisible until a command fails or you use `?` / `??`. Everything else passes through untouched.

```
  ┌─────────────────────────────┐
  │         You type...         │
  │   owd / ? list files / ??  │
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │      fix layer (zsh hooks)  │
  │                             │
  │  normal cmd ──→ pass through│
  │  failed cmd ──→ auto-correct│
  │  ? query   ──→ NL translate │
  │  ?? query  ──→ claude code  │
  └──────┬──────────┬───────────┘
         │          │
         │          │ only activates on
         │          │ failure, ? or ??
         │          │
         │    ┌─────▼─────────┐
         │    │   LLM layer   │
         │    │               │
         │    │ groq (fast)   │◄── auto-correct
         │    │ claude (smart)│◄── NL / long mode
         │    │               │
         │    └─────┬─────────┘
         │          │
         │   corrected / translated cmd
         │          │
         ▼          ▼
  ┌─────────────────────────────┐
  │       your real zsh         │
  │                             │
  │  colors, prompt, history,   │
  │  tab completion, ctrl+r     │
  │  — all untouched            │
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │     stdout / stderr         │
  │     back to you             │
  └─────────────────────────────┘
```

## Examples

### Auto-correct failed commands

Just type as usual. When a command fails, fix suggests and runs the correction:

```
💫 ➜  fix git:(main) owd
zsh: command not found: owd
-> pwd (via groq, openai/gpt-oss-20b, 283ms)
/Users/allaud/workspace/fix
```

### Natural language → shell command (`?`)

Describe what you want in plain English:

```
💫 ➜  fix git:(main) ? show me nested tree from here
-> tree -a --dirsfirst (via groq, llama-3.3-70b-versatile, 450ms)
.
├── fix_shell
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── countdown.py
│   ├── engine.py
│   ├── llm.py
│   ├── shell.py
│   └── spinner.py
├── fix.py
├── pyproject.toml
└── README.md
```

### Full Claude Code sessions (`??`)

For complex multi-step tasks:

```
💫 ➜  fix git:(main) ?? how many lines of py code here?
  [Bash] find . -path ./.venv -prune -o -name '*.py' -print | xargs wc -l
568 total across 10 Python files
```

## Installation

### Clone and alias (recommended)

```bash
git clone https://github.com/youruser/fix.git ~/fix
```

Add to your `~/.zshrc`:

```bash
alias fix="python3 ~/fix/fix.py"
```

Then open a new terminal and type `fix` to enter fix mode. Type `exit` to leave.

### Run directly

No install needed — just run with system python3:

```bash
python3 /path/to/fix/fix.py
```

## Usage

### Providers

fix uses two LLM providers:

- **groq** — free, fast models via [Groq API](https://console.groq.com). Great for auto-correction (~250ms)
- **claude_code** — uses your existing `claude` CLI. Smarter, better for natural language

By default, auto-correction uses Groq and natural language uses Claude Code. If Groq fails, it falls back to Claude Code automatically.

### Get a Groq API key (optional but recommended)

1. Sign up at [console.groq.com](https://console.groq.com)
2. Create an API key
3. Export it:

```bash
export GROQ_API_KEY="gsk_..."
```

Without a Groq key, everything falls back to Claude Code.

### Configuration

All settings can be set via environment variables, CLI arguments, or both. CLI args override env vars.

#### Environment variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Groq API key |
| `FIX_AC_PROVIDER` | `groq` | Auto-correction provider (`groq` or `claude_code`) |
| `FIX_AC_MODEL` | `llama-3.3-70b-versatile` | Auto-correction model |
| `FIX_AC_TIMEOUT` | `0` | Auto-correction autoaccept timeout (seconds) |
| `FIX_NL_PROVIDER` | `claude_code` | Natural language provider |
| `FIX_NL_MODEL` | `sonnet` | Natural language model |
| `FIX_NL_TIMEOUT` | `3` | Natural language autoaccept timeout (seconds) |
| `FIX_ICON` | `💫` | Prompt icon |

#### CLI arguments

```
--provider, -p        Set provider for both AC and NL
--model, -m           Set model for both AC and NL
--timeout, -t         Set autoaccept timeout for both AC and NL
--ac-provider         Auto-correction provider
--ac-model            Auto-correction model
--ac-timeout          Auto-correction autoaccept timeout
--nl-provider         Natural language provider
--nl-model            Natural language model
--nl-timeout          Natural language autoaccept timeout
--groq-key            Groq API key
--icon, -i            Prompt icon
```

#### Examples

```bash
# Use Groq for everything (fast and free)
fix -p groq

# Use Claude Code for everything
fix -p claude_code

# Groq for auto-correct, Claude for NL (default)
fix --ac-provider groq --nl-provider claude_code

# Custom model and 5s autoaccept for NL
fix --nl-model opus --nl-timeout 5

# Zero-delay auto-correction, 3s approval for NL
fix --ac-timeout 0 --nl-timeout 3

# Pass Groq key directly
fix --groq-key "gsk_..."
```

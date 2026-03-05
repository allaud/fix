import os
import sys
import time
import select
import subprocess

SPINNER_FRAMES = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]


def _run(cmd: str):
    subprocess.run(
        cmd,
        shell=True,
        executable=os.environ.get("SHELL", "/bin/zsh"),
    )


def countdown_and_run(cmd: str, seconds: int = 3):
    """Show spinner+countdown, then run command. Ctrl+c or n to cancel."""
    if seconds <= 0:
        _run(cmd)
        return

    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    approved = False
    try:
        tty.setcbreak(fd)
        frame_idx = 0
        for i in range(seconds, 0, -1):
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                frame = SPINNER_FRAMES[frame_idx % len(SPINNER_FRAMES)]
                sys.stdout.write(f"\r\033[1;35m{frame}\033[0m \033[1;33m{cmd}\033[0m \033[2m({i}s)\033[0m\033[K")
                sys.stdout.flush()
                frame_idx += 1
                ready, _, _ = select.select([sys.stdin], [], [], min(remaining, 0.08))
                if ready:
                    ch = sys.stdin.read(1)
                    sys.stdout.write("\r\033[K")
                    sys.stdout.flush()
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    if ch in ('\x03', 'n', 'N'):
                        print("\033[2mcancelled\033[0m")
                        return
                    approved = True
                    break
            if approved:
                break
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        approved = True
    except (KeyboardInterrupt, EOFError):
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("\033[2mcancelled\033[0m")
        return
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except termios.error:
            pass

    if approved:
        _run(cmd)

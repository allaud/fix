import sys
import time
import threading


FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner:
    def __init__(self, text: str = ""):
        self._text = text
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    def _spin(self):
        i = 0
        while not self._stop.is_set():
            frame = FRAMES[i % len(FRAMES)]
            sys.stdout.write(f"\r\033[1;35m{frame}\033[0m {self._text}")
            sys.stdout.flush()
            i += 1
            self._stop.wait(0.08)

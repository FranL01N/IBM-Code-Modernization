"""Minimal logging helpers used by the nightly report."""

import time

LOG_LINES: list[str] = []
DEBUG = False


def log(message: str) -> None:
    """Store and print a timestamped log message."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    LOG_LINES.append(line)
    print(line)


def debug(message: str) -> None:
    """Log a debug message when debug logging is enabled."""
    if DEBUG:
        log(f"DEBUG: {message}")


def flush_log(path: str) -> None:
    """Append buffered log lines to disk and clear the buffer."""
    with open(path, "a", encoding="utf-8") as file:
        for line in LOG_LINES:
            file.write(f"{line}\n")
    LOG_LINES.clear()

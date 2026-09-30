"""Load the legacy key-value settings file."""

SETTINGS_FILE = "settings.cfg"

KNOWN_KEYS = [
    "service_interval_km",
    "warn_at_percent",
    "report_title",
    "history_file",
    "log_file",
    "mileage_unit",
]


def load_settings(path: str | None = None) -> dict[str, str]:
    """Load recognized settings from a key-value configuration file."""
    settings_path = path if path is not None else SETTINGS_FILE
    settings: dict[str, str] = {}

    with open(settings_path, encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if key in KNOWN_KEYS:
                settings[key] = value.strip()

    return settings


def get_int(settings: dict[str, str], key: str, fallback: int) -> int:
    """Return an integer setting or a fallback when it is absent or invalid."""
    try:
        return int(settings[key])
    except (KeyError, ValueError):
        return fallback


def get_setting(settings: dict[str, str], key: str, fallback: str = "") -> str:
    """Return a string setting or its fallback."""
    return settings.get(key, fallback)

import os
from pathlib import Path

from app import create_app


def _load_local_env() -> None:
    """
    Load key=value pairs from .env into process env, without overriding
    variables already provided by the shell/host.
    """
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env()

app = create_app()

if __name__ == '__main__':
    app.run()

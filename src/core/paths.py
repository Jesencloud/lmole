from pathlib import Path


def get_config_dir() -> Path:
    return Path.home() / ".config" / "topo"

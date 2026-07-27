from pathlib import Path
import os
import shutil
import secrets
import sys

APP_NAME = "EasyPass"
LEGACY_APP_NAME = "".join(("PS", "Manager"))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        roaming = os.environ.get("APPDATA")
        base_dir = Path(roaming) if roaming else (Path.home() / "AppData" / "Roaming")
        return base_dir / APP_NAME
    return _repo_root() / "data"


DATA_DIR = Path(os.environ.get("EASYPASS_DATA_DIR") or _default_data_dir())
DB_PATH = str(DATA_DIR / "passwords.db")
KEY_FILE = str(DATA_DIR / ".key")
SECRET_KEY_FILE = DATA_DIR / "flask_secret.key"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _migrate_legacy_data_dir(target_dir: Path) -> None:
    if not getattr(sys, "frozen", False):
        return

    roaming = os.environ.get("APPDATA")
    base_dir = Path(roaming) if roaming else (Path.home() / "AppData" / "Roaming")
    legacy_dir = base_dir / LEGACY_APP_NAME
    if legacy_dir == target_dir or not legacy_dir.exists():
        return

    if (target_dir / "passwords.db").exists():
        return

    legacy_db = legacy_dir / "passwords.db"
    if not legacy_db.exists():
        return

    for item in legacy_dir.iterdir():
        dest = target_dir / item.name
        if dest.exists():
            continue
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


_migrate_legacy_data_dir(DATA_DIR)


def _load_or_create_secret_key() -> str:
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key.strip()

    if SECRET_KEY_FILE.exists():
        existing = SECRET_KEY_FILE.read_text(encoding="utf-8").strip()
        if existing:
            return existing

    key = secrets.token_urlsafe(32)
    SECRET_KEY_FILE.write_text(key, encoding="utf-8")
    return key


SECRET_KEY = _load_or_create_secret_key()

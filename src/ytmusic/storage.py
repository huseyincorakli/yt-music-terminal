import json
from pathlib import Path

from .models import Playlist, Track


CONFIG_DIR = Path.home() / ".config" / "ytmusic"
PLAYLISTS_FILE = CONFIG_DIR / "playlists.json"


def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _get_default_data() -> dict:
    default_id = "default"
    return {
        "default_id": default_id,
        "playlists": {default_id: {"name": "Favorites", "tracks": []}},
    }


def load_playlists() -> dict[str, Playlist]:
    _ensure_config_dir()

    if not PLAYLISTS_FILE.exists():
        data = _get_default_data()
        _write_default_data(data)

    with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    playlists = {}
    default_id = data.get("default_id", "default")

    for pid, pdata in data.get("playlists", {}).items():
        tracks = [Track(t["title"], t["video_id"]) for t in pdata.get("tracks", [])]
        playlists[pid] = Playlist(
            id=pid,
            name=pdata.get("name", "Unnamed"),
            tracks=tracks,
            is_default=(pid == default_id),
        )

    return playlists


def _write_default_data(data: dict) -> None:
    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_playlists(playlists: dict[str, Playlist], default_id: str) -> None:
    _ensure_config_dir()

    data = {"default_id": default_id, "playlists": {}}

    for pid, pl in playlists.items():
        data["playlists"][pid] = {
            "name": pl.name,
            "tracks": [{"title": t.title, "video_id": t.video_id} for t in pl.tracks],
        }

    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

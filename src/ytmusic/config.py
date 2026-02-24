"""Application configuration and constants."""

from pathlib import Path

# Paths
CONFIG_DIR = Path.home() / ".config" / "ytmusic"
PLAYLISTS_FILE = CONFIG_DIR / "playlists.json"

# MPV settings
MPV_SOCKET = "/tmp/ytmusic-mpv.sock"
MPV_VOLUME = 80
MPV_NO_VIDEO = True
MPV_REALLY_QUIET = True
MPV_TERM_OSD = "no"

# Socket settings
SOCKET_TIMEOUT = 0.2

# Thread pool
THREAD_POOL_WORKERS = 4

# UI settings
NOW_PLAYING_INTERVAL = 0.5
PROGRESS_BAR_WIDTH = 50

# Colors (hex)
COLORS = {
    "screen_bg": "#06060f",
    "header_bg": "#0c0c1e",
    "border": "#1e1e40",
    "logo": "#7b7bff",
    "search_bg": "#10101e",
    "search_focus": "#18183a",
    "text_primary": "#e0e0ff",
    "text_secondary": "#7070a0",
    "highlight_results": "#7b7bff",
    "highlight_queue": "#4dff88",
    "highlight_playlist": "#ff88ff",
    "dim": "#444468",
    "queue_bg": "#050510",
}

# Search settings
SEARCH_RESULTS = 10

# Key bindings (mode-based)
KEY_BINDINGS = {
    "normal": [
        ("/", "search"),
        ("enter", "play"),
        ("space", "pause"),
        ("n", "next"),
        ("a", "queue"),
        ("d", "dequeue"),
        ("l", "lists"),
        ("e", "add_def"),
        ("q", "quit"),
    ],
    "playlists": [
        ("l", "back"),
        ("enter", "open"),
        ("n", "new"),
        ("x", "delete"),
        ("/", "search"),
        ("q", "quit"),
    ],
    "playlist_tracks": [
        ("l", "back"),
        ("enter", "play"),
        ("n", "next"),
        ("d", "remove"),
        ("/", "search"),
        ("q", "quit"),
    ],
}

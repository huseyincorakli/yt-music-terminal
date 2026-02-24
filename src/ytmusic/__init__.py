"""YT Music TUI - Terminal-based YouTube Music Player."""

from .app import YTMusicApp, main
from .config import (
    CONFIG_DIR,
    PLAYLISTS_FILE,
    MPV_SOCKET,
    MPV_VOLUME,
    SOCKET_TIMEOUT,
    THREAD_POOL_WORKERS,
    NOW_PLAYING_INTERVAL,
    PROGRESS_BAR_WIDTH,
    COLORS,
    SEARCH_RESULTS,
    KEY_BINDINGS,
)
from .models import Track, Playlist
from .player import Player
from .storage import load_playlists, save_playlists
from .ui import (
    TrackListItem,
    PlaylistListItem,
    PlaylistTrackItem,
    QueueItem,
    NowPlayingBar,
    KeyBar,
)
from .utils import format_time

__all__ = [
    # App
    "YTMusicApp",
    "main",
    # Config
    "CONFIG_DIR",
    "PLAYLISTS_FILE",
    "MPV_SOCKET",
    "MPV_VOLUME",
    "SOCKET_TIMEOUT",
    "THREAD_POOL_WORKERS",
    "NOW_PLAYING_INTERVAL",
    "PROGRESS_BAR_WIDTH",
    "COLORS",
    "SEARCH_RESULTS",
    "KEY_BINDINGS",
    # Models
    "Track",
    "Playlist",
    # Player
    "Player",
    # Storage
    "load_playlists",
    "save_playlists",
    # UI
    "TrackListItem",
    "PlaylistListItem",
    "PlaylistTrackItem",
    "QueueItem",
    "NowPlayingBar",
    "KeyBar",
    # Utils
    "format_time",
]

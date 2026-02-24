"""UI widgets for YT Music application."""

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, Static

from ..models import Playlist, Track
from ..player import Player
from ..utils.formatters import format_time


class TrackListItem(ListItem):
    """List item for search results."""

    highlighted: reactive[bool] = reactive(False)

    def __init__(self, track: Track, index: int):
        super().__init__()
        self.track: Track = track
        self.index: int = index
        self._label: Label | None = None

    def compose(self) -> ComposeResult:
        yield Label(f"  {self.index + 1:>2}.  {self.track.title}")

    def _get_label(self) -> Label:
        if self._label is None:
            self._label = self.query_one(Label)
        return self._label

    def watch_highlighted(self, value: bool) -> None:
        label = self._get_label()
        if value:
            label.update(
                f"  [bold #7b7bff]{self.index + 1:>2}.  {self.track.title}[/bold #7b7bff]"
            )
        else:
            label.update(f"  {self.index + 1:>2}.  {self.track.title}")


class PlaylistListItem(ListItem):
    """List item for playlist selection."""

    highlighted: reactive[bool] = reactive(False)

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist: Playlist = playlist
        self._label: Label | None = None

    def compose(self) -> ComposeResult:
        icon = "⭐" if self.playlist.is_default else "🎵"
        count = len(self.playlist.tracks)
        name = f"{self.playlist.name} [dim]({count} tracks)[/dim]"
        yield Label(f"  {icon}  {name}")

    def _get_label(self) -> Label:
        if self._label is None:
            self._label = self.query_one(Label)
        return self._label

    def watch_highlighted(self, value: bool) -> None:
        label = self._get_label()
        icon = "⭐" if self.playlist.is_default else "🎵"
        count = len(self.playlist.tracks)
        if value:
            label.update(
                f"  [bold #ff88ff]{icon}  {self.playlist.name}[/bold #ff88ff] [dim]({count} tracks)[/dim]"
            )
        else:
            label.update(f"  {icon}  {self.playlist.name} [dim]({count} tracks)[/dim]")


class PlaylistTrackItem(ListItem):
    """List item for tracks in a playlist."""

    highlighted: reactive[bool] = reactive(False)

    def __init__(self, track: Track, index: int, playing: bool = False):
        super().__init__()
        self.track: Track = track
        self.index: int = index
        self.playing: bool = playing
        self._label: Label | None = None

    def compose(self) -> ComposeResult:
        icon = "[bold #4dff88]▶ [/bold #4dff88]" if self.playing else "   "
        yield Label(f"  {icon}{self.index + 1:>2}.  {self.track.title[:50]}")

    def _get_label(self) -> Label:
        if self._label is None:
            self._label = self.query_one(Label)
        return self._label

    def watch_highlighted(self, value: bool) -> None:
        label = self._get_label()
        if self.playing:
            icon = "[bold #4dff88]▶ [/bold #4dff88]"
            if value:
                label.update(
                    f"  {icon}[bold #4dff88]{self.index + 1:>2}.  {self.track.title[:50]}[/bold #4dff88]"
                )
            else:
                label.update(f"  {icon}{self.index + 1:>2}.  {self.track.title[:50]}")
        else:
            if value:
                label.update(
                    f"  [bold #ff88ff]{self.index + 1:>2}.  {self.track.title[:50]}[/bold #ff88ff]"
                )
            else:
                label.update(f"  {self.index + 1:>2}.  {self.track.title[:50]}")


class QueueItem(ListItem):
    """List item for queue."""

    highlighted: reactive[bool] = reactive(False)

    def __init__(self, track: Track, index: int, playing: bool = False):
        super().__init__()
        self.track: Track = track
        self.index: int = index
        self.playing: bool = playing
        self._label: Label | None = None

    def compose(self) -> ComposeResult:
        icon = "[bold #4dff88]▶ [/bold #4dff88]" if self.playing else "   "
        yield Label(f"  {icon}{self.index + 1:>2}.  {self.track.title[:42]}")

    def _get_label(self) -> Label:
        if self._label is None:
            self._label = self.query_one(Label)
        return self._label

    def watch_highlighted(self, value: bool) -> None:
        label = self._get_label()
        if self.playing:
            icon = "[bold #4dff88]▶ [/bold #4dff88]"
            if value:
                label.update(
                    f"  {icon}[bold #4dff88]{self.index + 1:>2}.  {self.track.title[:42]}[/bold #4dff88]"
                )
            else:
                label.update(f"  {icon}{self.index + 1:>2}.  {self.track.title[:42]}")
        else:
            if value:
                label.update(
                    f"  [bold #4dff88]{self.index + 1:>2}.  {self.track.title[:42]}[/bold #4dff88]"
                )
            else:
                label.update(f"  {self.index + 1:>2}.  {self.track.title[:42]}")


class NowPlayingBar(Widget):
    """Now playing display with progress bar."""

    track: reactive[Track | None] = reactive(None)
    paused: reactive[bool] = reactive(False)
    tick: reactive[int] = reactive(0)

    def __init__(self, player: Player, **kwargs):
        super().__init__(**kwargs)
        self._player = player

    def compose(self) -> ComposeResult:
        yield Static("", id="np-track")
        yield Static("", id="np-bar")

    def on_mount(self):
        from ..config import NOW_PLAYING_INTERVAL

        self.set_interval(NOW_PLAYING_INTERVAL, self._tick)

    def _tick(self):
        self.tick += 1
        self._draw()

    def _draw(self):
        try:
            track_w = self.query_one("#np-track", Static)
            bar_w = self.query_one("#np-bar", Static)
        except Exception:
            return

        if self.track is None:
            track_w.update(
                "  [dim #3a3a5a]◈  Nothing playing — press / to search[/dim #3a3a5a]"
            )
            bar_w.update("")
            return

        title = self.track.title
        max_len = 62
        if len(title) > max_len:
            padded = title + "   ·   " + title
            offset = self.tick % (len(title) + 7)
            title = padded[offset : offset + max_len]

        if self.paused:
            badge = "[on #3a0a0a][bold #ff6b6b] ⏸  PAUSED [/bold #ff6b6b][/on #3a0a0a]"
        else:
            dot = ["●", "○"][(self.tick // 3) % 2]
            badge = f"[on #0a2a14][bold #4dff88] {dot}  PLAYING [/bold #4dff88][/on #0a2a14]"

        track_w.update(f"  {badge}   [bold #dde0ff]{title}[/bold #dde0ff]")

        pos = self._player.position
        dur = self._player.duration

        if dur > 0:
            ratio = min(1.0, pos / dur)
            from ..config import PROGRESS_BAR_WIDTH

            BAR_W = PROGRESS_BAR_WIDTH
            filled = int(ratio * BAR_W)
            norm = ratio
            if norm < 0.5:
                r = int(60 + norm * 2 * 195)
                g = int(160 + norm * 2 * 70)
                b = 255
            else:
                r = 255
                g = int(230 - (norm - 0.5) * 2 * 200)
                b = int(255 - (norm - 0.5) * 2 * 255)
            col = f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"

            if filled < BAR_W:
                pb = (
                    f"[{col}]{'━' * filled}[/{col}]"
                    f"[bold #ffffff]◉[/bold #ffffff]"
                    f"[#1e1e40]{'╌' * (BAR_W - filled)}[/#1e1e40]"
                )
            else:
                pb = f"[{col}]{'━' * BAR_W}[/{col}]"

            bar_w.update(
                f"  [dim #444468]{format_time(pos)}[/dim #444468]  "
                f"{pb}  "
                f"[dim #444468]{format_time(dur)}[/dim #444468]"
            )
        else:
            from ..config import PROGRESS_BAR_WIDTH

            W = PROGRESS_BAR_WIDTH
            p = (self.tick * 3) % (W + 12)
            dot_p = max(0, min(W - 3, p - 6))
            pb = (
                f"[#1a1a38]{'╌' * dot_p}[/#1a1a38]"
                f"[bold #5577ff]━━━[/bold #5577ff]"
                f"[#1a1a38]{'马斯' * max(0, W - dot_p - 3)}[/#1a1a38]"
            )
            bar_w.update(
                f"  [dim #333355]0:00[/dim #333355]  {pb}  [dim #333355]loading...[/dim #333355]"
            )

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, Static

from .models import Track
from .player import Player


class TrackListItem(ListItem):
    """List item for search results."""
    
    def __init__(self, track: Track, index: int):
        super().__init__()
        self.track = track
        self.index = index

    def compose(self) -> ComposeResult:
        yield Label(f"  {self.index + 1:>2}.  {self.track.title}")


class QueueItem(ListItem):
    """List item for queue."""
    
    def __init__(self, track: Track, index: int, playing: bool = False):
        super().__init__()
        self.track = track
        self.index = index
        self.playing = playing

    def compose(self) -> ComposeResult:
        icon = "[bold #4dff88]▶ [/bold #4dff88]" if self.playing else "   "
        yield Label(f"  {icon}{self.index + 1:>2}.  {self.track.title[:42]}")

    def watch_highlighted(self, value: bool) -> None:
        if value and self.playing:
            self.query_one(Label).update(
                f"  [bold #4dff88]▶ [/bold #4dff88][bold #4dff88]{self.index + 1:>2}.  {self.track.title[:42]}[/bold #4dff88]"
            )
        elif self.playing:
            self.query_one(Label).update(
                f"  [bold #4dff88]▶ [/bold #4dff88]{self.index + 1:>2}.  {self.track.title[:42]}"
            )


def fmt_time(secs: float) -> str:
    """Format seconds to mm:ss."""
    secs = max(0, int(secs))
    m, s = divmod(secs, 60)
    return f"{m}:{s:02d}"


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
        self.set_interval(0.25, self._tick)

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
            track_w.update("  [dim #3a3a5a]◈  Nothing playing — press / to search[/dim #3a3a5a]")
            bar_w.update("")
            return

        title = self.track.title
        max_len = 62
        if len(title) > max_len:
            padded = title + "   ·   " + title
            offset = self.tick % (len(title) + 7)
            title = padded[offset:offset + max_len]

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
            BAR_W = 50
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
            col = f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"

            if filled < BAR_W:
                pb = (
                    f"[{col}]{'━' * filled}[/{col}]"
                    f"[bold #ffffff]◉[/bold #ffffff]"
                    f"[#1e1e40]{'╌' * (BAR_W - filled)}[/#1e1e40]"
                )
            else:
                pb = f"[{col}]{'━' * BAR_W}[/{col}]"

            bar_w.update(
                f"  [dim #444468]{fmt_time(pos)}[/dim #444468]  "
                f"{pb}  "
                f"[dim #444468]{fmt_time(dur)}[/dim #444468]"
                f"   [dim #333355]{int(ratio*100):>3}%[/dim #333355]"
            )
        else:
            W = 50
            p = (self.tick * 3) % (W + 12)
            dot_p = max(0, min(W - 3, p - 6))
            pb = (
                f"[#1a1a38]{'╌' * dot_p}[/#1a1a38]"
                f"[bold #5577ff]━━━[/bold #5577ff]"
                f"[#1a1a38]{'╌' * max(0, W - dot_p - 3)}[/#1a1a38]"
            )
            bar_w.update(f"  [dim #333355]0:00[/dim #333355]  {pb}  [dim #333355]loading...[/dim #333355]")


class KeyBar(Static):
    """Key bindings display."""
    
    KEYS = [
        ("/", "search"),
        ("↵", "play"),
        ("spc", "pause"),
        ("n", "next"),
        ("a", "queue"),
        ("d", "dequeue"),
        ("esc", "results"),
        ("q", "quit"),
    ]

    def render(self) -> str:
        parts = [
            f"[reverse #7b7bff] {k} [/reverse #7b7bff][dim #555577] {label} [/dim #555577]"
            for k, label in self.KEYS
        ]
        return " " + " ".join(parts)

import subprocess

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual import work, on
from textual.widgets import Input, Label, ListView, Static

from .models import Track
from .player import Player
from .widgets import TrackListItem, QueueItem, NowPlayingBar, KeyBar


class YTMusicApp(App):
    """YT Music Terminal Player."""
    
    CSS = """
    Screen { background: #06060f; }

    #root { layout: vertical; height: 100%; }

    /* HEADER */
    #header {
        height: 3;
        background: #0c0c1e;
        border-bottom: tall #1e1e40;
        layout: horizontal;
        align: left middle;
        padding: 0 2;
    }
    #logo {
        width: auto;
        color: #7b7bff;
        text-style: bold;
        margin-right: 3;
    }
    #search-input {
        width: 1fr; height: 1;
        border: none;
        background: #10101e;
        color: #e0e0ff;
        padding: 0 2;
        margin: 1 0;
    }
    #search-input:focus {
        border: none;
        background: #18183a;
        color: #ffffff;
    }

    /* MAIN */
    #main { layout: horizontal; height: 1fr; }

    /* RESULTS */
    #results-panel { width: 2fr; border-right: tall #161630; }
    #results-header {
        height: 2;
        background: #0c0c1e;
        color: #44446a;
        padding: 0 2;
        content-align: left middle;
        border-bottom: tall #131330;
    }
    #results-list {
        height: 1fr;
        background: #06060f;
        scrollbar-color: #1e1e40;
        scrollbar-background: #06060f;
    }
    #results-list > ListItem {
        background: #06060f; height: 2; padding: 0;
    }
    #results-list > ListItem:hover { background: #0e0e20; }
    #results-list > ListItem.--highlight {
        background: #10102a;
        border-left: tall #7b7bff;
    }
    #results-list Label {
        color: #7070a0; height: 2; content-align: left middle;
    }
    #results-list > ListItem.--highlight Label {
        color: #d0d0ff; text-style: bold;
    }

    /* QUEUE */
    #queue-panel { width: 1fr; background: #050510; }
    #queue-header {
        height: 2;
        background: #0c0c1e;
        color: #44446a;
        padding: 0 2;
        content-align: left middle;
        border-bottom: tall #131330;
    }
    #queue-list {
        height: 1fr;
        background: #050510;
        scrollbar-color: #131328;
        scrollbar-background: #050510;
    }
    #queue-list > ListItem {
        background: #050510; height: 2; padding: 0;
    }
    #queue-list > ListItem:hover { background: #0c0c22; }
    #queue-list > ListItem.--highlight {
        background: #0e0e28;
        border-left: tall #4dff88;
    }
    #queue-list Label {
        color: #484870; height: 2; content-align: left middle;
    }
    #queue-list > ListItem.--highlight Label {
        color: #4dff88; text-style: bold;
    }

    /* NOW PLAYING */
    #now-playing {
        height: 6;
        background: #0a0a1e;
        border-top: tall #1e1e45;
        layout: vertical;
        padding: 1 2;
    }
    #np-track { height: 2; content-align: left middle; }
    #np-bar   { height: 2; content-align: left middle; }

    /* KEY BAR */
    #keybar {
        height: 2;
        background: #07070f;
        border-top: tall #131328;
        content-align: left middle;
        padding: 0 2;
    }

    /* LOADING */
    #loading {
        display: none;
        height: 1fr;
        content-align: center middle;
        color: #5555cc;
        text-style: italic;
    }
    #loading.visible { display: block; }
    """

    BINDINGS = [
        Binding("/", "focus_search", "Search", show=False),
        Binding("space", "toggle_pause", "Pause", show=False),
        Binding("n", "next_track", "Next", show=False),
        Binding("a", "add_to_queue", "Queue", show=False),
        Binding("d", "remove_from_queue", "Dequeue", show=False),
        Binding("escape", "focus_results", "Results", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.player = Player()
        self.player.on_finish = self._on_track_finish
        self.results: list[Track] = []
        self.queue: list[Track] = []
        self.queue_index = 0
        self._finishing = False

    def compose(self) -> ComposeResult:
        with Vertical(id="root"):
            with Horizontal(id="header"):
                yield Label("▶ YT MUSIC", id="logo")
                yield Input(placeholder="  Search for a song, artist or album...", id="search-input")
            with Horizontal(id="main"):
                with Vertical(id="results-panel"):
                    yield Static("  Results", id="results-header")
                    yield Static("", id="loading")
                    yield ListView(id="results-list")
                with Vertical(id="queue-panel"):
                    yield Static("  ♫  Queue", id="queue-header")
                    yield ListView(id="queue-list")
            yield NowPlayingBar(self.player, id="now-playing")
            yield KeyBar(id="keybar")

    def on_mount(self):
        self.query_one("#search-input").focus()

    # ── Search ──────────────────────────────────

    def action_focus_search(self):
        self.query_one("#search-input").focus()

    def action_focus_results(self):
        lst = self.query_one("#results-list", ListView)
        if len(lst) > 0:
            lst.focus()

    @on(Input.Submitted, "#search-input")
    async def on_search_submit(self, event: Input.Submitted):
        query = event.value.strip()
        if query:
            await self._do_search(query)

    @work(exclusive=True, thread=True)
    def _search_worker(self, query: str):
        try:
            r = subprocess.run(
                ["yt-dlp", f"ytsearch10:{query}",
                 "--get-title", "--get-id", "--flat-playlist", "--no-warnings"],
                capture_output=True, text=True, timeout=30
            )
            lines = [line.strip() for line in r.stdout.splitlines() if line.strip()]
            tracks = [Track(lines[i], lines[i+1]) for i in range(0, len(lines)-1, 2)]
            self.call_from_thread(self._show_results, tracks)
        except Exception as e:
            self.call_from_thread(self._show_error, str(e))

    async def _do_search(self, query: str):
        loading = self.query_one("#loading", Static)
        rl = self.query_one("#results-list", ListView)
        loading.update(f'\n\n  ◌  Searching for "{query}"...')
        loading.add_class("visible")
        rl.clear()
        rl.display = False
        self._search_worker(query)
        self.query_one("#results-header", Static).update(f'  Results  [dim]— {query}[/dim]')

    def _show_results(self, tracks: list[Track]):
        self.results = tracks
        loading = self.query_one("#loading", Static)
        rl = self.query_one("#results-list", ListView)
        loading.remove_class("visible")
        rl.display = True
        rl.clear()
        for i, t in enumerate(tracks):
            rl.append(TrackListItem(t, i))
        if tracks:
            rl.focus()
            self.query_one("#results-header", Static).update(
                f"  Results  [dim]— {len(tracks)} found[/dim]"
            )
        else:
            loading.update("  No results found.")
            loading.add_class("visible")

    def _show_error(self, err: str):
        loading = self.query_one("#loading", Static)
        loading.update(f"  ✗  Error: {err}")
        loading.add_class("visible")

    # ── Playback ────────────────────────────────

    @on(ListView.Selected, "#results-list")
    def on_result_selected(self, event: ListView.Selected):
        if isinstance(event.item, TrackListItem):
            self._play(event.item.track)

    @on(ListView.Selected, "#queue-list")
    def on_queue_selected(self, event: ListView.Selected):
        if isinstance(event.item, QueueItem):
            self.queue_index = event.item.index
            self._play(self.queue[self.queue_index])

    def _play(self, track: Track):
        self._finishing = False
        self.player.play(track)
        bar = self.query_one("#now-playing", NowPlayingBar)
        bar.track = track
        bar.paused = False
        self._redraw_queue()

    def action_toggle_pause(self):
        if self.player.is_playing or self.player.is_paused:
            self.player.toggle_pause()
            bar = self.query_one("#now-playing", NowPlayingBar)
            bar.paused = self.player.is_paused

    def action_next_track(self):
        if not self.queue:
            return
        self.queue_index = (self.queue_index + 1) % len(self.queue)
        self._play(self.queue[self.queue_index])

    def _on_track_finish(self):
        if not self.queue or self._finishing:
            return
        self._finishing = True
        next_index = (self.queue_index + 1) % len(self.queue)
        self.queue_index = next_index
        self.call_from_thread(self._play, self.queue[self.queue_index])

    # ── Queue ────────────────────────────────────

    def action_add_to_queue(self):
        rl = self.query_one("#results-list", ListView)
        if rl.highlighted_child is None:
            return
        item = rl.highlighted_child
        if not isinstance(item, TrackListItem):
            return
        track = item.track
        if any(t.video_id == track.video_id for t in self.queue):
            self.notify("Already in queue", severity="warning", timeout=2)
            return
        self.queue.append(track)
        self._redraw_queue()
        self.notify(f"Added: {track.title[:40]}", timeout=2)

    def action_remove_from_queue(self):
        ql = self.query_one("#queue-list", ListView)
        if ql.highlighted_child is None:
            return
        item = ql.highlighted_child
        if not isinstance(item, QueueItem):
            return
        idx = item.index
        if 0 <= idx < len(self.queue):
            del self.queue[idx]
            if self.queue_index >= len(self.queue):
                self.queue_index = max(0, len(self.queue) - 1)
            self._redraw_queue()

    def _redraw_queue(self):
        ql = self.query_one("#queue-list", ListView)
        current_id = self.player.current.video_id if self.player.current else None
        ql.clear()
        for i, t in enumerate(self.queue):
            ql.append(QueueItem(t, i, playing=(t.video_id == current_id)))
        n = len(self.queue)
        self.query_one("#queue-header", Static).update(
            f"  ♫  Queue  [dim]— {n} track{'s' if n != 1 else ''}[/dim]" if n else "  ♫  Queue"
        )

    def on_unmount(self):
        self.player.stop()


def main():
    YTMusicApp().run()

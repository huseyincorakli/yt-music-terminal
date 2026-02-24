import asyncio
import uuid

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual import work, on
from textual.widgets import Input, Label, ListView, Static, Button

from .config import SEARCH_RESULTS
from .models import Playlist, Track
from .player import Player
from .storage import load_playlists, save_playlists
from .ui import (
    PlaylistListItem,
    PlaylistTrackItem,
    TrackListItem,
    QueueItem,
    NowPlayingBar,
    KeyBar,
)


class YTMusicApp(App):
    """YT Music Terminal Player."""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("/", "focus_search", "Search", show=False),
        Binding("space", "toggle_pause", "Pause", show=False),
        Binding("n", "next_track", "Next", show=False),
        Binding("a", "add_to_queue", "Queue", show=False),
        Binding("d", "remove_from_queue", "Dequeue", show=False),
        Binding("l", "toggle_lists", "Lists", show=False),
        Binding("e", "add_to_default", "AddDef", show=False),
        Binding("y", "add_to_playlist", "AddList", show=False),
        Binding("x", "delete_playlist", "Delete", show=False),
        Binding("escape", "handle_escape", "Back", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.player: Player = Player()
        self.player.on_finish = self._on_track_finish
        self.results: list[Track] = []
        self.queue: list[Track] = []
        self.queue_index: int = 0
        self._finishing: bool = False

        self.playlists: dict[str, Playlist] = load_playlists()
        self._list_mode: str = "normal"
        self._current_playlist_id: str | None = None
        self._pending_delete_id: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="root"):
            with Horizontal(id="header"):
                yield Label("▶ YT MUSIC", id="logo")
                yield Input(
                    placeholder="  Search for a song, artist or album...",
                    id="search-input",
                )
            with Horizontal(id="main"):
                with Vertical(id="results-panel"):
                    yield Static("  Results", id="results-header")
                    yield Static("", id="loading")
                    yield ListView(id="results-list")
                with Vertical(id="queue-panel"):
                    yield Static("  ♫  Queue", id="queue-header")
                    yield ListView(id="queue-list")
                with Vertical(id="playlist-panel"):
                    yield Static("  🎵  Playlists", id="playlist-header")
                    yield ListView(id="playlist-list")
                    with Vertical(id="playlist-input-container", classes="hidden"):
                        yield Input(
                            placeholder="  Playlist name...", id="playlist-name-input"
                        )
                        with Horizontal(id="playlist-input-buttons"):
                            yield Button(
                                "Create", id="playlist-create-btn", variant="primary"
                            )
                            yield Button("Cancel", id="playlist-cancel-btn")
            yield NowPlayingBar(self.player, id="now-playing")
            yield KeyBar(id="keybar")

    def on_mount(self):
        self.query_one("#search-input").focus()
        self._show_playlist_panel(False)
        self._redraw_playlists()
        self.query_one("#playlist-input-container").display = False

    # ── Playlist ─────────────────────────────────

    def _show_playlist_panel(self, show: bool):
        panel = self.query_one("#playlist-panel")
        panel.display = show

    def _redraw_playlists(self):
        pl = self.query_one("#playlist-list", ListView)
        pl.clear()
        for playlist in self.playlists.values():
            pl.append(PlaylistListItem(playlist))

    def _redraw_playlist_tracks(self, playlist_id: str):
        pl = self.query_one("#playlist-list", ListView)
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return
        pl.clear()
        current_id = self.player.current.video_id if self.player.current else None
        for i, track in enumerate(playlist.tracks):
            pl.append(
                PlaylistTrackItem(track, i, playing=(track.video_id == current_id))
            )

    def action_toggle_lists(self):
        if self._list_mode == "normal":
            self._list_mode = "playlists"
            self._current_playlist_id = None
            self._show_playlist_panel(True)
            self._hide_results_queue(True)
            self._redraw_playlists()
            self.query_one("#playlist-header", Static).update("  🎵  Listeler")
            pl = self.query_one("#playlist-list", ListView)
            if len(pl) > 0:
                pl.focus()
            self._update_keybar()
        elif self._list_mode == "playlists":
            if self._current_playlist_id:
                self._list_mode = "playlists"
                self._current_playlist_id = None
                self._redraw_playlists()
                self.query_one("#playlist-header", Static).update("  🎵  Listeler")
            else:
                self._exit_list_mode()
        elif self._list_mode == "playlist_tracks":
            self._list_mode = "playlists"
            self._current_playlist_id = None
            self._redraw_playlists()
            self.query_one("#playlist-header", Static).update("  🎵  Listeler")
            pl = self.query_one("#playlist-list", ListView)
            if len(pl) > 0:
                pl.focus()
            self._update_keybar()

    def _exit_list_mode(self):
        self._list_mode = "normal"
        self._current_playlist_id = None
        self._show_playlist_panel(False)
        self._hide_results_queue(False)
        self._update_keybar()
        self.query_one("#search-input").focus()

    def _update_keybar(self):
        kb = self.query_one("#keybar", KeyBar)
        kb._mode = self._list_mode
        kb.refresh()

    def _hide_results_queue(self, hide: bool):
        self.query_one("#results-panel").display = not hide
        self.query_one("#queue-panel").display = not hide

    def action_handle_escape(self):
        if self._list_mode != "normal":
            self.action_toggle_lists()
        else:
            self.action_focus_results()

    @on(ListView.Selected, "#playlist-list")
    def on_playlist_selected(self, event: ListView.Selected):
        if isinstance(event.item, PlaylistListItem):
            playlist = event.item.playlist
            self._list_mode = "playlist_tracks"
            self._current_playlist_id = playlist.id
            self._redraw_playlist_tracks(playlist.id)
            self.query_one("#playlist-header", Static).update(f"  🎵  {playlist.name}")
            self._update_keybar()
        elif isinstance(event.item, PlaylistTrackItem):
            if self._list_mode == "playlist_tracks" and self._current_playlist_id:
                self.queue_index = event.item.index
                self._play(event.item.track, from_playlist=True)

    def action_add_to_default(self):
        default_id = None
        for pid, pl in self.playlists.items():
            if pl.is_default:
                default_id = pid
                break
        if default_id is None:
            default_id = "default"
        self._add_to_playlist(default_id)

    def action_new_playlist(self):
        if self._list_mode != "playlists":
            return
        self._show_playlist_input()

    def _show_playlist_input(self):
        input_container = self.query_one("#playlist-input-container")
        input_field = self.query_one("#playlist-name-input", Input)
        input_container.display = True
        input_field.focus()

    def _hide_playlist_input(self):
        input_container = self.query_one("#playlist-input-container")
        input_field = self.query_one("#playlist-name-input", Input)
        input_field.value = ""
        input_container.display = False

    @on(Input.Submitted, "#playlist-name-input")
    def _on_playlist_name_submit(self, event: Input.Submitted):
        name = event.value.strip()
        if name:
            new_id = str(uuid.uuid4())[:8]
            self.playlists[new_id] = Playlist(id=new_id, name=name, tracks=[])
            save_playlists(self.playlists, self._get_default_id())
            self._redraw_playlists()
            self.notify(f"Created: {name}", timeout=2)
        self._hide_playlist_input()

    @on(Button.Pressed, "#playlist-cancel-btn")
    def _on_cancel_playlist(self):
        self._hide_playlist_input()

    @on(Button.Pressed, "#playlist-create-btn")
    def _on_create_playlist(self):
        input_field = self.query_one("#playlist-name-input", Input)
        name = input_field.value.strip()
        if name:
            new_id = str(uuid.uuid4())[:8]
            self.playlists[new_id] = Playlist(id=new_id, name=name, tracks=[])
            save_playlists(self.playlists, self._get_default_id())
            self._redraw_playlists()
            self.notify(f"Created: {name}", timeout=2)
        self._hide_playlist_input()

    def action_add_to_playlist(self):
        self.notify("Select a playlist first (press y in list mode)", timeout=2)

    def action_delete_playlist(self):
        if self._list_mode != "playlists":
            return
        pl = self.query_one("#playlist-list", ListView)
        if pl.highlighted_child is None:
            return
        item = pl.highlighted_child
        if not isinstance(item, PlaylistListItem):
            return
        playlist = item.playlist
        if playlist.is_default:
            self.notify(
                "Cannot delete default playlist!", severity="warning", timeout=2
            )
            return
        if self._pending_delete_id == playlist.id:
            del self.playlists[playlist.id]
            save_playlists(self.playlists, self._get_default_id())
            self._redraw_playlists()
            self._pending_delete_id = None
            self.notify(f"'{playlist.name}' deleted", timeout=2)
        else:
            self._pending_delete_id = playlist.id
            self.notify(
                f"'{playlist.name}' will be deleted! Press 'x' again to confirm",
                timeout=3,
            )

    def action_confirm_delete(self):
        pass

    def _add_to_playlist(self, playlist_id: str):
        rl = self.query_one("#results-list", ListView)
        if rl.highlighted_child is None:
            return
        item = rl.highlighted_child
        if not isinstance(item, TrackListItem):
            return
        track = item.track
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return
        if any(t.video_id == track.video_id for t in playlist.tracks):
            self.notify("Already in playlist", severity="warning", timeout=2)
            return
        playlist.tracks.append(track)
        save_playlists(self.playlists, self._get_default_id())
        self.notify(f"Added: {track.title[:30]}", timeout=2)

    def _get_default_id(self) -> str:
        for pid, pl in self.playlists.items():
            if pl.is_default:
                return pid
        return "default"

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

    @work(exclusive=True)
    async def _search_worker(self, query: str):
        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                f"ytsearch10:{query}",
                "--get-title",
                "--get-id",
                "--flat-playlist",
                "--no-warnings",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode()
            lines = [line.strip() for line in output.splitlines() if line.strip()]
            tracks = [
                Track(lines[i], lines[i + 1]) for i in range(0, len(lines) - 1, 2)
            ]
            self._show_results(tracks)
        except Exception as e:
            self._show_error(str(e))

    async def _do_search(self, query: str):
        loading = self.query_one("#loading", Static)
        rl = self.query_one("#results-list", ListView)
        loading.update(f'\n\n  ◌  Searching for "{query}"...')
        loading.add_class("visible")
        rl.clear()
        rl.display = False
        self._search_worker(query)
        self.query_one("#results-header", Static).update(
            f"  Results  [dim]— {query}[/dim]"
        )

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

    def _play(self, track: Track, from_playlist: bool = False):
        self._finishing = False
        self.player.play(track)
        bar = self.query_one("#now-playing", NowPlayingBar)
        bar.track = track
        bar.paused = False
        if not from_playlist:
            self._redraw_queue()
        if self._list_mode == "playlist_tracks" and self._current_playlist_id:
            self._redraw_playlist_tracks(self._current_playlist_id)

    def action_toggle_pause(self):
        if self.player.is_playing or self.player.is_paused:
            self.player.toggle_pause()
            bar = self.query_one("#now-playing", NowPlayingBar)
            bar.paused = self.player.is_paused

    def action_next_track(self):
        if self._list_mode == "playlists":
            self._show_playlist_input()
        elif self._list_mode == "playlist_tracks" and self._current_playlist_id:
            playlist = self.playlists.get(self._current_playlist_id)
            if not playlist or not playlist.tracks:
                return
            self.queue_index = (self.queue_index + 1) % len(playlist.tracks)
            self._play(playlist.tracks[self.queue_index], from_playlist=True)
        elif not self.queue:
            return
        else:
            self.queue_index = (self.queue_index + 1) % len(self.queue)
            self._play(self.queue[self.queue_index])

    def _on_track_finish(self):
        if self._list_mode == "playlist_tracks" and self._current_playlist_id:
            playlist = self.playlists.get(self._current_playlist_id)
            if not playlist or not playlist.tracks or self._finishing:
                return
            self._finishing = True
            self.queue_index = (self.queue_index + 1) % len(playlist.tracks)
            self.call_from_thread(self._play, playlist.tracks[self.queue_index], True)
        elif not self.queue or self._finishing:
            return
        else:
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
        if self._list_mode == "playlist_tracks" and self._current_playlist_id:
            pl = self.query_one("#playlist-list", ListView)
            if pl.highlighted_child is None:
                return
            item = pl.highlighted_child
            if not isinstance(item, PlaylistTrackItem):
                return
            playlist = self.playlists.get(self._current_playlist_id)
            if not playlist:
                return
            idx = item.index
            if 0 <= idx < len(playlist.tracks):
                del playlist.tracks[idx]
                save_playlists(self.playlists, self._get_default_id())
                self._redraw_playlist_tracks(self._current_playlist_id)
                self.notify("Track removed from playlist", timeout=2)
        else:
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
            f"  ♫  Queue  [dim]— {n} track{'s' if n != 1 else ''}[/dim]"
            if n
            else "  ♫  Queue"
        )

    def on_unmount(self):
        save_playlists(self.playlists, self._get_default_id())
        self.player.stop()


def main():
    YTMusicApp().run()

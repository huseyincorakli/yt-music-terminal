import json
import signal
import socket
import subprocess
import threading
import time
from typing import Optional, Callable

from .models import Track


MPV_SOCKET = "/tmp/ytmusic-mpv.sock"


class Player:
    """Audio player using mpv with IPC control."""
    
    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._paused = False
        self._current: Optional[Track] = None
        self._pos_running = False
        self.position: float = 0.0
        self.duration: float = 0.0
        self.on_finish: Optional[Callable[[], None]] = None

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._proc is not None and self._proc.poll() is None

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def current(self) -> Optional[Track]:
        return self._current

    def play(self, track: Track) -> None:
        """Play a track."""
        self._stop_proc()
        self._current = track
        self._paused = False
        self.position = 0.0
        self.duration = 0.0
        with self._lock:
            self._proc = subprocess.Popen(
                ["mpv", "--no-video", "--really-quiet", "--term-osd=no",
                 "--volume=80", f"--input-ipc-server={MPV_SOCKET}", track.url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        self._pos_running = True
        threading.Thread(target=self._monitor, daemon=True).start()
        threading.Thread(target=self._poll, daemon=True).start()

    def _stop_proc(self) -> None:
        """Stop the current mpv process."""
        self._pos_running = False
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            self._proc = None

    def stop(self) -> None:
        """Stop playback."""
        self._stop_proc()
        self._current = None
        self._paused = False
        self.position = 0.0
        self.duration = 0.0

    def toggle_pause(self) -> None:
        """Toggle pause/resume."""
        with self._lock:
            if self._proc and self._proc.poll() is None:
                if self._paused:
                    self._proc.send_signal(signal.SIGCONT)
                    self._paused = False
                else:
                    self._proc.send_signal(signal.SIGSTOP)
                    self._paused = True

    def _ipc(self, cmd: dict) -> Optional[dict]:
        """Send IPC command to mpv."""
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(MPV_SOCKET)
            s.sendall((json.dumps(cmd) + "\n").encode())
            data = s.recv(4096).decode()
            s.close()
            for line in data.splitlines():
                try:
                    r = json.loads(line)
                    if "data" in r:
                        return r
                except Exception:
                    pass
        except Exception:
            pass
        return None

    def _poll(self) -> None:
        """Poll mpv for position and duration."""
        time.sleep(2)
        while self._pos_running:
            if not self.is_playing:
                break
            r = self._ipc({"command": ["get_property", "time-pos"]})
            if r and isinstance(r.get("data"), (int, float)):
                self.position = float(r["data"])
            r = self._ipc({"command": ["get_property", "duration"]})
            if r and isinstance(r.get("data"), (int, float)):
                self.duration = float(r["data"])
            time.sleep(0.5)

    def _monitor(self) -> None:
        """Monitor process exit."""
        proc = self._proc
        if proc:
            proc.wait()
            with self._lock:
                still_current = self._proc is proc
            if still_current and self.on_finish and not self._paused:
                self._pos_running = False
                self.on_finish()

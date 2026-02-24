from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    """Represents a YouTube track."""

    title: str
    video_id: str

    @property
    def url(self) -> str:
        return f"https://youtube.com/watch?v={self.video_id}"


@dataclass
class Playlist:
    """Represents a playlist."""

    id: str
    name: str
    tracks: list[Track] = field(default_factory=list)
    is_default: bool = False

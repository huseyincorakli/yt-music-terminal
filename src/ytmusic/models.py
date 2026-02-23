from dataclasses import dataclass


@dataclass
class Track:
    """Represents a YouTube track."""
    
    title: str
    video_id: str

    @property
    def url(self) -> str:
        return f"https://youtube.com/watch?v={self.video_id}"

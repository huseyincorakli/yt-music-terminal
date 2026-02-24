"""KeyBar widget for displaying keyboard shortcuts."""

from textual.widgets import Static

from ..config import KEY_BINDINGS


class KeyBar(Static):
    """Key bindings display."""

    _mode: str = "normal"

    def render(self) -> str:
        mode = getattr(self, "_mode", "normal")
        keys = KEY_BINDINGS.get(mode, KEY_BINDINGS["normal"])
        parts = [
            f"[reverse #7b7bff] {k} [/reverse #7b7bff][dim #555577] {label} [/dim #555577]"
            for k, label in keys
        ]
        return " " + " ".join(parts)

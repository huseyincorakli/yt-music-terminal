"""Utility functions for formatting."""


def format_time(secs: float) -> str:
    """Format seconds to mm:ss."""
    secs = max(0, int(secs))
    m, s = divmod(secs, 60)
    return f"{m}:{s:02d}"

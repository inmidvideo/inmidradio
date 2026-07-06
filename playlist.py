"""Pure playlist helpers, kept free of any Discord dependency so they can be
unit-tested without mocking voice clients."""

from __future__ import annotations

import os

MUSIC_EXTENSION = ".mp3"


def load_playlist(directory: str) -> list[str]:
    """Return the mp3 filenames in ``directory``, sorted alphabetically."""
    return sorted(f for f in os.listdir(directory) if f.lower().endswith(MUSIC_EXTENSION))


def next_index(current: int, length: int) -> int:
    """Return the next track index, wrapping back to 0 at the end.

    Returns 0 when the playlist is empty so callers never divide by zero.
    """
    if length <= 0:
        return 0
    return (current + 1) % length

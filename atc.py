"""Pure helpers for resolving LiveATC feeds, kept free of any Discord or network
dependency so they can be unit-tested in isolation.

LiveATC serves a small ``.pls`` playlist per feed at
``/play/<feed>.pls`` whose ``File1=`` line points at the live MP3 stream. That
endpoint is not behind the Cloudflare challenge that guards the search page, so
the bot can resolve a feed server-side. Feed IDs (e.g. ``kord1s1_atis``) are not
derivable from an ICAO code; the user supplies the exact ID.
"""

from __future__ import annotations

import re

# LiveATC mount names are lowercase alphanumerics plus underscores. Restricting
# to this set also keeps user input from injecting anything into the URL.
_FEED_RE = re.compile(r"^[a-z0-9_]+$")
_ICAO_PREFIX_RE = re.compile(r"^[a-z]{1,4}")


def normalize_feed(raw: str) -> str:
    """Lowercase and trim a user-supplied feed ID."""
    return raw.strip().lower()


def is_valid_feed(feed: str) -> bool:
    """Return whether ``feed`` is a syntactically valid LiveATC mount name."""
    return bool(_FEED_RE.match(feed))


def pls_url(feed: str) -> str:
    """Return the LiveATC ``.pls`` playlist URL for ``feed``."""
    return f"https://www.liveatc.net/play/{feed}.pls"


def parse_pls(text: str) -> str | None:
    """Return the first stream URL from a ``.pls`` file, or None if absent.

    A ``.pls`` for a non-existent or empty feed still returns HTTP 200 but with a
    blank ``File1=``, so callers must treat None as "no live feed".
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("file1="):
            url = stripped.split("=", 1)[1].strip()
            return url or None
    return None


def icao_hint(feed: str) -> str:
    """Best-effort ICAO guess from a feed ID, for building a help link.

    Feed IDs start with the airport's ICAO code (``kord1s1_atis`` -> ``kord``).
    """
    match = _ICAO_PREFIX_RE.match(feed)
    return match.group(0) if match else feed


def search_url(feed: str) -> str:
    """Return the LiveATC search page URL for the airport ``feed`` belongs to."""
    return f"https://www.liveatc.net/search/?icao={icao_hint(feed)}"

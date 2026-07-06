from atc import (
    icao_hint,
    is_valid_feed,
    normalize_feed,
    parse_pls,
    pls_url,
    search_url,
)

SAMPLE_PLS = """[playlist]
File1=http://d.liveatc.net/kord1s1_atis
Title1=KORD ATIS
Length1=-1
NumberOfEntries=1
"""

EMPTY_PLS = """[playlist]
File1=
Title1=
Length1=-1
NumberOfEntries=1
"""


def test_normalize_feed_trims_and_lowercases():
    assert normalize_feed("  KORD1S1_ATIS  ") == "kord1s1_atis"


def test_is_valid_feed_accepts_mount_names():
    assert is_valid_feed("kord1s1_atis")
    assert is_valid_feed("klax_twr")


def test_is_valid_feed_rejects_bad_input():
    assert not is_valid_feed("kord twr")  # space
    assert not is_valid_feed("../etc/passwd")  # path traversal
    assert not is_valid_feed("kord;rm")  # shell metachar
    assert not is_valid_feed("")


def test_pls_url():
    assert pls_url("kord1s1_atis") == "https://www.liveatc.net/play/kord1s1_atis.pls"


def test_parse_pls_returns_stream_url():
    assert parse_pls(SAMPLE_PLS) == "http://d.liveatc.net/kord1s1_atis"


def test_parse_pls_empty_feed_returns_none():
    assert parse_pls(EMPTY_PLS) is None


def test_parse_pls_missing_file_returns_none():
    assert parse_pls("[playlist]\nNumberOfEntries=0\n") is None


def test_icao_hint_extracts_airport_prefix():
    assert icao_hint("kord1s1_atis") == "kord"
    assert icao_hint("klax_twr") == "klax"


def test_search_url_points_at_airport():
    assert search_url("kord1s1_atis") == "https://www.liveatc.net/search/?icao=kord"

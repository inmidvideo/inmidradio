from playlist import load_playlist, next_index


def test_load_playlist_filters_and_sorts(tmp_path):
    for name in ["b.mp3", "a.mp3", "c.txt", "d.MP3", "cover.jpg"]:
        (tmp_path / name).touch()

    assert load_playlist(str(tmp_path)) == ["a.mp3", "b.mp3", "d.MP3"]


def test_load_playlist_empty(tmp_path):
    assert load_playlist(str(tmp_path)) == []


def test_next_index_advances():
    assert next_index(0, 3) == 1
    assert next_index(1, 3) == 2


def test_next_index_wraps_to_start():
    assert next_index(2, 3) == 0


def test_next_index_empty_playlist_is_safe():
    assert next_index(0, 0) == 0

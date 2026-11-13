import pytest

pytest.importorskip("mosaicolabs")  # cloud only: installed by `just cloud-setup`

from starter.mosaico import build_query, parse_meta


def test_parse_meta():
    assert parse_meta(["team=team-01", " robot = so101 "]) == [
        ("team", "team-01"),
        ("robot", "so101"),
    ]


def test_parse_meta_rejects_missing_equals():
    with pytest.raises(ValueError):
        parse_meta(["team"])


def test_build_query_without_filters_lists_everything():
    assert build_query() is None


def test_build_query_with_filters():
    assert build_query(name="team-01_*", task="Pick up*", meta=[("team", "team-01")]) is not None

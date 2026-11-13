import json

import pytest

from starter.cli import main
from starter.lerobot_check import video_features


def _dataset(tmp_path, image_dtype):
    (tmp_path / "meta").mkdir()
    features = {
        "observation.state": {"dtype": "float32", "shape": [6]},
        "observation.images.front": {"dtype": image_dtype, "shape": [480, 640, 3]},
    }
    (tmp_path / "meta" / "info.json").write_text(json.dumps({"features": features}))
    return tmp_path


def test_images_in_parquet_pass(tmp_path):
    ds = _dataset(tmp_path, "image")
    assert video_features(ds) == []
    assert main(["check", str(ds)]) == 0


def test_videos_are_reported(tmp_path):
    ds = _dataset(tmp_path, "video")
    assert video_features(ds) == ["observation.images.front"]
    assert main(["check", str(ds)]) == 1


def test_missing_dataset(tmp_path):
    with pytest.raises(FileNotFoundError):
        video_features(tmp_path)

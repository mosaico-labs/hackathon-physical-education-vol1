"""Check a local LeRobot dataset before pushing it to Mosaico.

Mosaico's LeRobot injector reads images embedded in the parquet files and skips video features,
so a dataset recorded with MP4 videos would lose its cameras. Record with `--dataset.video=false`
(what `just record` does) to store the images in parquet.
"""

import json
from pathlib import Path


def load_info(dataset_dir: Path) -> dict:
    info = Path(dataset_dir) / "meta" / "info.json"
    if not info.is_file():
        raise FileNotFoundError(f"no LeRobot dataset at {dataset_dir} (missing meta/info.json)")
    return json.loads(info.read_text())


def video_features(dataset_dir: Path) -> list[str]:
    """Names of the features stored as MP4 videos (must be empty to push to Mosaico)."""
    features = load_info(dataset_dir).get("features", {})
    return sorted(k for k, f in features.items() if f.get("dtype") == "video")

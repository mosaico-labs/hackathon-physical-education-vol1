"""Thin helpers around the Mosaico SDK: connect, search sequences, export to LeRobot."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from mosaicolabs import MosaicoClient, QuerySequence

from starter.config import Settings, get_settings

# Metadata written by the LeRobot injector lives under the reserved `_lerobot_` namespace.
# The task strings of an episode are stored under `_lerobot_.<...>.tasks`.
TASK_KEY = "_lerobot_.*.tasks"


@contextmanager
def connect(settings: Settings | None = None) -> Iterator[MosaicoClient]:
    s = settings or get_settings()
    client = MosaicoClient.connect(s.host, s.port, api_key=s.api_key, tls_cert_path=s.tls_cert)
    try:
        yield client
    finally:
        client.close()


def parse_meta(pairs: Sequence[str]) -> list[tuple[str, str]]:
    """Turn ["key=glob", ...] into [(key, glob), ...]."""
    out = []
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise ValueError(f"expected KEY=GLOB, got {pair!r}")
        out.append((key.strip(), value.strip()))
    return out


def build_query(
    name: str | None = None,
    task: str | None = None,
    meta: Sequence[tuple[str, str]] = (),
) -> QuerySequence | None:
    """Build a sequence query; returns None when no filter is given (= list everything)."""
    if not (name or task or meta):
        return None
    q = QuerySequence()
    if name:
        q = q.with_name_match(name)
    if task:
        q = q.with_user_metadata(TASK_KEY, match=task)
    for key, value in meta:
        q = q.with_user_metadata(key, match=value)
    return q


def find_sequences(
    client: MosaicoClient,
    name: str | None = None,
    task: str | None = None,
    meta: Sequence[tuple[str, str]] = (),
) -> list[str]:
    """Sorted names of the sequences matching all the given filters."""
    query = build_query(name, task, meta)
    if query is None:
        return sorted(client.list_sequences())
    results = client.query(query) or []
    return sorted({item.sequence.name for item in results})


def export_lerobot(
    sequence_names: Sequence[str],
    out: Path,
    overwrite: bool = False,
    settings: Settings | None = None,
):
    """Rebuild a LeRobot v3 dataset under `out`, one episode per sequence."""
    from mosaicolabs.bridges.lerobot.sequences_extractor import (
        LeRobotExtractorConfig,
        LeRobotSequencesExtractor,
    )

    s = settings or get_settings()
    config = LeRobotExtractorConfig(
        saving_path=out,
        sequence_names=list(sequence_names),
        host=s.host,
        port=s.port,
        mosaico_api_key=s.api_key,
        tls_cert_path=s.tls_cert,
        overwrite=overwrite,
    )
    return LeRobotSequencesExtractor(config).run()

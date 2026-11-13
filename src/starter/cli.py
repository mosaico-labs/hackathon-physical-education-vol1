"""`starter` command line: ping the server, search sequences, export them as a LeRobot dataset.

starter ping
starter sequences [--name GLOB] [--task GLOB] [--meta KEY=GLOB ...] [--details] [--json]
starter extract OUT [--name GLOB] [--task GLOB] [--meta KEY=GLOB ...] [--seq NAME ...]
starter check DIR
"""

import argparse
import json
import os
import sys
from pathlib import Path

from starter.config import get_settings
from starter.lerobot_check import video_features


def _add_filters(p: argparse.ArgumentParser) -> None:
    p.add_argument("--name", help="glob on the sequence name, e.g. 'team-01_*'")
    p.add_argument("--task", help="glob on the LeRobot task text, e.g. 'Pick up*'")
    p.add_argument(
        "--meta",
        action="append",
        default=[],
        metavar="KEY=GLOB",
        help="glob on any user-metadata key (repeatable, AND-ed), e.g. team=team-01",
    )


def cmd_ping(_: argparse.Namespace) -> int:
    from starter.mosaico import connect

    s = get_settings()
    with connect(s) as client:
        info = client.info()
        n = len(client.list_sequences())
    print(f"Connected to mosaicod {info.version} at {s.host}:{s.port} — {n} sequences")
    return 0


def cmd_sequences(args: argparse.Namespace) -> int:
    from starter.mosaico import connect, find_sequences, parse_meta

    with connect() as client:
        names = find_sequences(client, args.name, args.task, parse_meta(args.meta))
        rows = []
        for name in names:
            row = {"name": name}
            if args.details:
                h = client.sequence_handler(name)
                if h is not None:
                    row |= {
                        "topics": len(h.topics),
                        "size_mb": round(h.total_size_bytes / 1e6, 1),
                        "user_metadata": {
                            k: v for k, v in h.user_metadata.items() if k != "_lerobot_"
                        },
                    }
            rows.append(row)

    if args.json:
        json.dump(rows, sys.stdout, indent=2, default=str)
        print()
    elif not rows:
        print("No sequence matches.", file=sys.stderr)
        return 1
    else:
        for row in rows:
            extra = "  ".join(f"{k}={v}" for k, v in row.items() if k != "name")
            print(f"{row['name']}  {extra}".rstrip())
        print(f"\n{len(rows)} sequence(s)", file=sys.stderr)
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    from starter.mosaico import connect, export_lerobot, find_sequences, parse_meta

    names = list(args.seq)
    if args.name or args.task or args.meta:
        with connect() as client:
            names += find_sequences(client, args.name, args.task, parse_meta(args.meta))
    names = sorted(set(names))
    if not names:
        print("Nothing to extract: give --seq or a filter that matches something.", file=sys.stderr)
        return 1

    print(f"Exporting {len(names)} sequence(s) to {args.out}")
    export_lerobot(names, args.out, overwrite=args.overwrite)
    print(f"Done. Train on it with: just train {args.out.name}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    videos = video_features(args.dir)
    if videos:
        print(
            f"❌ {args.dir} stores {', '.join(videos)} as MP4 video, which Mosaico cannot ingest.\n"
            "   Re-record with `just record`: it sets --dataset.video=false (images in parquet).",
            file=sys.stderr,
        )
        return 1
    print(f"✅ {args.dir}: images are stored in parquet")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="starter", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ping", help="check the Mosaico connection").set_defaults(fn=cmd_ping)

    p = sub.add_parser("sequences", help="list / search sequences")
    _add_filters(p)
    p.add_argument("--details", action="store_true", help="also fetch size, topics and metadata")
    p.add_argument("--json", action="store_true", help="print JSON")
    p.set_defaults(fn=cmd_sequences)

    p = sub.add_parser("extract", help="export sequences as a LeRobot v3 dataset")
    p.add_argument("out", type=Path, help="output dataset folder")
    _add_filters(p)
    p.add_argument("--seq", action="append", default=[], help="explicit sequence name")
    p.add_argument("--overwrite", action="store_true", help="replace OUT if it exists")
    p.set_defaults(fn=cmd_extract)

    p = sub.add_parser("check", help="check a local dataset can be pushed (images in parquet)")
    p.add_argument("dir", type=Path, help="LeRobot dataset folder")
    p.set_defaults(fn=cmd_check)

    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # keep CLI errors short; set STARTER_DEBUG=1 for the traceback
        if os.environ.get("STARTER_DEBUG"):
            raise
        s = get_settings()
        print(f"error ({s.host}:{s.port}): {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

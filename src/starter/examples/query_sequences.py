"""Minimal example: query Mosaico sequences with the raw SDK, then export them to LeRobot.

Run with:  just example
Edit the query below to explore the data other teams have pushed.
"""

from pathlib import Path

from mosaicolabs import QuerySequence

from starter.mosaico import connect, export_lerobot  # noqa: F401

OUT = Path("data/example_export")


def main() -> None:
    with connect() as client:
        results = client.query(
            QuerySequence()
            # .with_name_match("team-01_*")
            .with_user_metadata("_lerobot_.*.tasks", match="Pick up*")
        )
        if not results:
            print("No sequence matches.")
            return

        names = sorted(item.sequence.name for item in results)
        print("\n".join(names))

    # Uncomment to rebuild a LeRobot dataset from the matches:
    # export_lerobot(names, OUT, overwrite=True)


if __name__ == "__main__":
    main()

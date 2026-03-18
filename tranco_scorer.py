"""Tranco-driven domain scorer for the expiry pipeline."""

import argparse
import csv
import io
import random
import sys
import urllib.request
import zipfile
from pathlib import Path

TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"
DEFAULT_OUTPUT = "expiry/domains.csv"
DEFAULT_POOL = 500
DEFAULT_SAMPLE = 50


def filter_it(rows):
    """Return rows where domain ends with '.it'."""
    return [(rank, domain) for rank, domain in rows if domain.endswith(".it")]


def score(rank: int, domain: str) -> float:
    """score = 1/rank + 1/len(sld)."""
    sld = domain.rsplit(".", 1)[0]
    return 1 / rank + 1 / len(sld)


def select(rows, pool: int, sample: int) -> list:
    """Score rows, take top `pool`, randomly sample `sample`."""
    scored = sorted(rows, key=lambda r: score(r[0], r[1]), reverse=True)

    if len(scored) < pool:
        print(
            f"Warning: only {len(scored)} .it domains available, less than pool={pool}. Using all.",
            file=sys.stderr,
        )
        pool = len(scored)

    candidates = scored[:pool]

    if sample > pool:
        print(
            f"Warning: sample={sample} exceeds pool={pool}. Clamping sample to {pool}.",
            file=sys.stderr,
        )
        sample = pool

    return random.sample(candidates, sample)


def write_csv(domains, output_path) -> None:
    """Write domains in expiry/domains.csv format."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["domain", "expiration_date", "notes"])
        writer.writeheader()
        for rank, domain in domains:
            writer.writerow({"domain": domain, "expiration_date": "", "notes": f"tranco:{rank}"})


def download_tranco(url: str = TRANCO_URL) -> list:
    """Download and parse Tranco top-1M zip. Returns list of (rank, domain)."""
    with urllib.request.urlopen(url) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
            return [(int(rank), domain) for rank, domain in reader]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score .it domains from Tranco top-1M")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--pool", type=int, default=DEFAULT_POOL)
    parser.add_argument("--sample", type=int, default=DEFAULT_SAMPLE)
    args = parser.parse_args(argv)

    try:
        rows = download_tranco()
    except Exception as e:
        print(f"Error: failed to download Tranco list: {e}", file=sys.stderr)
        sys.exit(1)

    it_rows = filter_it(rows)
    selected = select(it_rows, pool=args.pool, sample=args.sample)
    write_csv(selected, args.output)


if __name__ == "__main__":
    main()

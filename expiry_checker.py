import csv
import datetime
import sys
import tempfile
from pathlib import Path

import whois_client


def run(input_path: Path, today: datetime.date | None = None) -> None:
    if today is None:
        today = datetime.date.today()

    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames if reader.fieldnames is not None else ["domain", "expiration_date", "notes"]
        rows = list(reader)

    # Deduplicate: keep first occurrence, warn on duplicates
    seen: set[str] = set()
    deduped: list[dict] = []
    for row in rows:
        domain = row["domain"]
        if domain.lower() in seen:
            print(f"Warning: duplicate domain '{domain}' ignored", file=sys.stderr)
        else:
            seen.add(domain.lower())
            deduped.append(row)

    # Backfill missing expiry dates via WHOIS
    for row in deduped:
        if not row.get("expiration_date"):
            result = whois_client.expiry_date(row["domain"])
            if result is not None:
                row["expiration_date"] = result.isoformat()
            else:
                print(f"Warning: could not fetch expiry for '{row['domain']}'", file=sys.stderr)

    # Atomic write-back of input file
    tmp = input_path.with_suffix(".tmp")
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(deduped)
        tmp.replace(input_path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    # Compute days_remaining and filter
    expiring: list[dict] = []
    for row in deduped:
        if not row.get("expiration_date"):
            continue
        expiry = datetime.date.fromisoformat(row["expiration_date"])
        days = (expiry - today).days
        if days <= 30:
            expiring.append({
                "domain": row["domain"],
                "expiration_date": row["expiration_date"],
                "days_remaining": days,
                "notes": row.get("notes", ""),
            })

    expiring.sort(key=lambda r: r["days_remaining"])

    # Write output
    out_dir = input_path.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today.isoformat()}-expiring.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["domain", "expiration_date", "days_remaining", "notes"])
        writer.writeheader()
        writer.writerows(expiring)


if __name__ == "__main__":
    run(input_path=Path(__file__).resolve().parent / "expiry" / "domains.csv")

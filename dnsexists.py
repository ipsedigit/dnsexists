import csv
import importlib
import logging
import sys
import time
from pathlib import Path

import whois_client

logger = logging.getLogger(__name__)

TLDS = [
    ".com", ".net", ".org", ".io", ".co",
    ".ai", ".dev", ".app", ".it", ".eu",
    ".info", ".biz", ".me", ".online", ".store",
    ".shop", ".tech", ".news", ".club", ".xyz",
]


def is_available(domain: str) -> bool:
    return not whois_client.is_registered(domain)


def check_domains(name: str, tlds: list[str], delay: float = 1.0) -> list[str]:
    available = []
    for tld in tlds:
        domain = name + tld
        logger.info("Checking %s...", domain)
        if is_available(domain):
            available.append(domain)
            logger.info("%s: available", domain)
        else:
            logger.info("%s: taken", domain)
        time.sleep(delay)
    return available


def _root() -> Path:
    return Path(__file__).parent


def _output_dir() -> Path:
    return _root() / "output"


def _parse_arg(args: list[str], flag: str) -> str | None:
    try:
        return args[args.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def _write_input_csv(path: Path, candidates: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (["name"] + [k for k in candidates[0] if k != "name"]) if candidates else ["name"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in candidates:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def synthesize(scored: list[tuple[float, str]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ranked = sorted(scored, key=lambda x: (-x[0], x[1]))[:10]
    with open(out_dir / "insight.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["domain", "score"])
        writer.writeheader()
        for score, domain in ranked:
            writer.writerow({"domain": domain, "score": score})


def write_results(name: str, available_domains: list[str], tlds: list[str], out_dir: Path | None = None) -> Path:
    resolved = out_dir if out_dir is not None else _output_dir()
    resolved.mkdir(parents=True, exist_ok=True)
    out_path = resolved / f"{name}.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["domain", "tld"])
        writer.writeheader()
        for tld in tlds:
            domain = name + tld
            if domain in available_domains:
                writer.writerow({"domain": domain, "tld": tld})
    return out_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = sys.argv[1:]
    field = _parse_arg(args, "--field")

    root = _root()
    name = _parse_arg(args, "--name")

    if not field and not name:
        print("Usage: python dnsexists.py --name <name>")
        print("       python dnsexists.py --field dev")
        sys.exit(2)

    if not field:
        # standalone mode
        available = check_domains(name, TLDS)
        if not available:
            print(f"No domains available for {name}")
            sys.exit(1)
        write_results(name, available, TLDS, out_dir=root / "output")
        print(f"Results written to output/{name}.csv")
        sys.exit(0)

    if field != "dev":
        print(f"Unknown field: {field}. Supported: dev")
        sys.exit(2)

    try:
        field_mod = importlib.import_module(f"fields.{field}")
    except ModuleNotFoundError:
        print(f"Unknown field: {field}")
        sys.exit(2)

    candidates = field_mod.fetch({})
    _write_input_csv(root / field / "input" / "candidates.csv", candidates)

    if not candidates:
        logger.warning("No candidates returned by %s.fetch()", field)
        sys.exit(0)

    names = field_mod.select(candidates)
    if not names:
        logger.warning("No names returned by %s.select()", field)
        sys.exit(0)

    out_dir = root / field / "output"
    names_set = set(names)
    scored: list[tuple[float, str]] = []
    for candidate in candidates:
        name = candidate["name"]
        score = candidate["score"]
        if name not in names_set:
            continue
        available = check_domains(name, TLDS)
        write_results(name, available, TLDS, out_dir=out_dir)
        for domain in available:
            scored.append((score, domain))
    synthesize(scored, out_dir=out_dir / "insight")
    sys.exit(0)


if __name__ == "__main__":
    main()

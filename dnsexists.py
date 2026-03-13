import csv
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


def _output_dir() -> Path:
    return Path(__file__).parent / "output"


def write_results(name: str, available_domains: list[str], tlds: list[str]) -> Path:
    out_dir = _output_dir()
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{name}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["domain", "tld", "available"])
        writer.writeheader()
        for tld in tlds:
            domain = name + tld
            writer.writerow({
                "domain": domain,
                "tld": tld,
                "available": "true" if domain in available_domains else "false",
            })
    return out_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) != 2:
        print("Usage: python dnsexists.py <name>")
        sys.exit(2)
    name = sys.argv[1]
    available = check_domains(name, TLDS)
    if not available:
        print(f"No domains available for {name}")
        sys.exit(1)
    write_results(name, available, TLDS)
    print(f"Results written to output/{name}.csv")
    sys.exit(0)


if __name__ == "__main__":
    main()

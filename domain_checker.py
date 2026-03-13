import csv
import sys
from pathlib import Path

import dns.resolver

TLDS = [
    ".com", ".net", ".org", ".io", ".co",
    ".ai", ".dev", ".app", ".it", ".eu",
    ".info", ".biz", ".me", ".online", ".store",
    ".shop", ".tech", ".news", ".club", ".xyz",
]


def is_available(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, "NS")
        return False
    except dns.resolver.NXDOMAIN:
        return True
    except Exception:
        return False


def check_domains(name: str, tlds: list[str]) -> list[str]:
    return [name + tld for tld in tlds if is_available(name + tld)]


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
    if len(sys.argv) != 2:
        print("Usage: python domain_checker.py <name>")
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

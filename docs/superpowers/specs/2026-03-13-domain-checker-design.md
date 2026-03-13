---
title: Domain Checker — DEV-8
date: 2026-03-13
card: DEV-8
---

# Design: Domain Availability Checker

## Summary

Given a name string (e.g. `myapp`), check availability of `name+tld` for 20 common TLDs by querying **NS records** via `dnspython`. A domain with no NS records is considered available. If at least one domain is available, write a CSV report to `output/<name>.csv`. Implemented as a new `domain_checker.py` module; `dnsexists.py` is unchanged.

## Why NS Records (not A records)

Every registered domain has NS records assigned by the registrar, even if it has no web server or A record. An NXDOMAIN on an NS query is a strong signal the domain is unregistered. Using `socket.getaddrinfo()` (A/AAAA records) would produce false positives — registered-but-parked domains would appear available.

## Architecture

```
dnsexists/
├── dnsexists.py                    # existing — unchanged
├── domain_checker.py               # new — is_available(), check_domains(), write_results(), main()
├── requirements.txt                # add: dnspython>=2.0
├── output/                         # created at runtime, gitignored
└── tests/
    └── test_domain_checker.py      # new
```

## TLD List (hardcoded constant)

```python
TLDS = [
    ".com", ".net", ".org", ".io", ".co",
    ".ai", ".dev", ".app", ".it", ".eu",
    ".info", ".biz", ".me", ".online", ".store",
    ".shop", ".tech", ".news", ".club", ".xyz",
]
```

## Components

### `is_available(domain: str) -> bool`

- Uses `dns.resolver.resolve(domain, "NS")` from `dnspython`
- Returns `False` if NS records are found (domain is registered)
- Returns `True` if `dns.resolver.NXDOMAIN` is raised (exact import: `from dns.resolver import NXDOMAIN`)
- Returns `False` conservatively for any other exception (e.g. `dns.resolver.NoNameservers`, `dns.resolver.Timeout`) — treat ambiguous results as "taken" to avoid false positives

### `check_domains(name: str, tlds: list[str]) -> list[str]`

- Iterates over `tlds`, builds `name + tld` for each
- Calls `is_available(domain)` for each
- Returns list of domains where `is_available()` returned `True`

### `write_results(name: str, available_domains: list[str], tlds: list[str]) -> Path`

- `tlds` is always passed as `TLDS` by `main()` so all 20 TLDs appear in the output
- Creates `output/` directory relative to the script file: `Path(__file__).parent / "output"`, using `.mkdir(exist_ok=True)`
- Writes `output/<name>.csv` with header `domain,tld,available`
- One row per TLD in `tlds` order — `available` = `true` if `name+tld` is in `available_domains`, `false` otherwise
- Returns the output `Path`

### `main()`

- Accepts one positional CLI argument: the name string
- Calls `check_domains(name, TLDS)`
- If no domains are available: prints `"No domains available for <name>"` and exits with code 1. No file written.
- If ≥1 domain available: calls `write_results(name, available, TLDS)`, prints `"Results written to output/<name>.csv"` and exits with code 0

## CLI Usage

```bash
python domain_checker.py myapp
# → output/myapp.csv (if any domain available)
```

## Output File Format

```
domain,tld,available
myapp.com,.com,false
myapp.io,.io,true
...
```

Row order matches `TLDS` constant order.

## Input Constraints

- `name` is assumed to be a valid DNS label: no dots, slashes, spaces, or empty string. No validation is performed — garbage in, garbage out.

## Error Handling

- Missing argument: print usage message, exit 2
- `dns.resolver.NXDOMAIN` → available (`True`)
- Any other DNS exception → treat as taken (`False`) — conservative, avoids false positives
- `write_results` I/O errors propagate — no special exit code

## Testing

- `test_is_available_returns_true_on_nxdomain` — mock `dns.resolver.resolve` to raise `NXDOMAIN`
- `test_is_available_returns_false_on_answer` — mock resolver returning NS records
- `test_is_available_returns_false_on_other_exception` — mock `NoNameservers`, assert returns `False`
- `test_check_domains_returns_available_domains` — mock `is_available()` selectively
- `test_check_domains_returns_empty_when_all_taken` — mock all `is_available()` returning `False`
- `test_write_results_creates_csv` — assert file exists with correct header, rows in TLDS order
- `test_main_no_args_exits_2`
- `test_main_no_available_domains_exits_1` — mock `check_domains` returning `[]`
- `test_main_writes_file_when_available` — mock `check_domains`, assert file written

## Constraints

- Python 3.12
- `dnspython>=2.0` added to `requirements.txt`
- `output/` added to `.gitignore`

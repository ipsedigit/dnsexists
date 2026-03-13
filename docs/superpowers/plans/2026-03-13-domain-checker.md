# Domain Checker Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `domain_checker.py` — a CLI tool that checks DNS availability of a name across 20 TLDs using NS-record queries and writes available domains to a CSV file.

**Architecture:** `is_available()` queries NS records via `dnspython` (NXDOMAIN = available, any other exception = taken). `check_domains()` iterates TLDs calling `is_available()`. `write_results()` writes `output/<name>.csv` relative to the script file. `main()` wires them together.

**Tech Stack:** Python 3.12, `dnspython>=2.0`, `pytest`

> **Note:** Do NOT run `git commit` or `git push`. User handles all git operations.

---

## Chunk 1: Setup and `is_available()`

### Task 1: Add dnspython to requirements and gitignore output/

**Files:**
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Add `dnspython>=2.0` to `requirements.txt`**

Final content of `requirements.txt`:
```
dnspython>=2.0
```

- [ ] **Step 2: Add `output/` to `.gitignore`**

Append this line to `.gitignore`:
```
output/
```

- [ ] **Step 3: Install dnspython**

```bash
pip install dnspython
```

Expected: installs without error.

---

### Task 2: Implement `is_available()` with TDD

**Files:**
- Create: `tests/test_domain_checker.py`
- Create: `domain_checker.py`

- [ ] **Step 1: Write failing tests for `is_available()`**

Create `C:\repo\dnsexists\tests\test_domain_checker.py`:
```python
from unittest.mock import patch
import dns.resolver
import pytest
from domain_checker import is_available


def test_is_available_returns_true_on_nxdomain():
    with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN):
        assert is_available("definitely-not-registered-xyz.com") is True


def test_is_available_returns_false_when_ns_records_found():
    with patch("dns.resolver.resolve", return_value=["ns1.example.com"]):
        assert is_available("google.com") is False


def test_is_available_returns_false_on_other_exception():
    # Use a plain Exception to avoid constructor issues with dns exception subclasses
    with patch("dns.resolver.resolve", side_effect=Exception("DNS error")):
        assert is_available("some-domain.com") is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_domain_checker.py -v
```

Expected: `ImportError: cannot import name 'is_available' from 'domain_checker'` (or `ModuleNotFoundError`)

- [ ] **Step 3: Create `domain_checker.py` with stub**

Create `C:\repo\dnsexists\domain_checker.py`:
```python
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
    raise NotImplementedError


def check_domains(name: str, tlds: list[str]) -> list[str]:
    raise NotImplementedError


def write_results(name: str, available_domains: list[str], tlds: list[str]) -> Path:
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they fail with NotImplementedError**

```bash
pytest tests/test_domain_checker.py -v
```

Expected: 4 FAILED with `NotImplementedError`

- [ ] **Step 5: Implement `is_available()`**

Replace the `is_available` stub:
```python
def is_available(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, "NS")
        return False
    except dns.resolver.NXDOMAIN:
        return True
    except Exception:
        return False
```

- [ ] **Step 6: Run `is_available()` tests to verify they pass**

```bash
pytest tests/test_domain_checker.py::test_is_available_returns_true_on_nxdomain tests/test_domain_checker.py::test_is_available_returns_false_when_ns_records_found tests/test_domain_checker.py::test_is_available_returns_false_on_other_exception -v
```

Expected: 3 PASSED

---

## Chunk 2: `check_domains()` and `write_results()`

### Task 3: Implement `check_domains()` with TDD

**Files:**
- Modify: `tests/test_domain_checker.py`
- Modify: `domain_checker.py`

- [ ] **Step 1: Add failing tests for `check_domains()`**

Append to `tests/test_domain_checker.py`:
```python
from domain_checker import check_domains


def test_check_domains_returns_available_domains():
    tlds = [".com", ".io", ".org"]
    # .com taken, .io available, .org taken
    availability = {
        "myapp.com": False,
        "myapp.io": True,
        "myapp.org": False,
    }
    with patch("domain_checker.is_available", side_effect=lambda d: availability[d]):
        result = check_domains("myapp", tlds)
    assert result == ["myapp.io"]


def test_check_domains_returns_empty_when_all_taken():
    tlds = [".com", ".io"]
    with patch("domain_checker.is_available", return_value=False):
        result = check_domains("myapp", tlds)
    assert result == []
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_domain_checker.py::test_check_domains_returns_available_domains tests/test_domain_checker.py::test_check_domains_returns_empty_when_all_taken -v
```

Expected: 2 FAILED with `NotImplementedError`

- [ ] **Step 3: Implement `check_domains()`**

Replace the `check_domains` stub:
```python
def check_domains(name: str, tlds: list[str]) -> list[str]:
    return [name + tld for tld in tlds if is_available(name + tld)]
```

- [ ] **Step 4: Run to verify they pass**

```bash
pytest tests/test_domain_checker.py::test_check_domains_returns_available_domains tests/test_domain_checker.py::test_check_domains_returns_empty_when_all_taken -v
```

Expected: 2 PASSED

---

### Task 4: Implement `write_results()` with TDD

**Files:**
- Modify: `tests/test_domain_checker.py`
- Modify: `domain_checker.py`

- [ ] **Step 1: Add failing test for `write_results()`**

Append to `tests/test_domain_checker.py`:
```python
import csv as csv_module
from domain_checker import write_results


def test_write_results_creates_csv(tmp_path, monkeypatch):
    import domain_checker
    # Redirect output dir to tmp_path
    monkeypatch.setattr(domain_checker, "_output_dir", lambda: tmp_path)
    tlds = [".com", ".io", ".org"]
    available = ["myapp.io"]
    path = write_results("myapp", available, tlds)
    assert path.exists()
    with open(path) as f:
        rows = list(csv_module.DictReader(f))
    assert len(rows) == 3
    assert rows[0] == {"domain": "myapp.com", "tld": ".com", "available": "false"}
    assert rows[1] == {"domain": "myapp.io", "tld": ".io", "available": "true"}
    assert rows[2] == {"domain": "myapp.org", "tld": ".org", "available": "false"}
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_domain_checker.py::test_write_results_creates_csv -v
```

Expected: FAILED with `NotImplementedError`

- [ ] **Step 3: Implement `_output_dir()` helper and `write_results()`**

Replace the `write_results` stub (and add `_output_dir` helper before it):
```python
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
```

- [ ] **Step 4: Run to verify it passes**

```bash
pytest tests/test_domain_checker.py::test_write_results_creates_csv -v
```

Expected: PASSED

---

## Chunk 3: `main()` and full integration

### Task 5: Implement `main()` with TDD

**Files:**
- Modify: `tests/test_domain_checker.py`
- Modify: `domain_checker.py`

- [ ] **Step 1: Add failing tests for `main()`**

Append to `tests/test_domain_checker.py`:
```python
from domain_checker import main


def test_main_no_args_exits_2(monkeypatch):
    monkeypatch.setattr("sys.argv", ["domain_checker.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_main_no_available_domains_exits_1(monkeypatch):
    monkeypatch.setattr("sys.argv", ["domain_checker.py", "myapp"])
    with patch("domain_checker.check_domains", return_value=[]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1


def test_main_writes_file_when_available(monkeypatch, tmp_path):
    import domain_checker as dc
    monkeypatch.setattr("sys.argv", ["domain_checker.py", "myapp"])
    monkeypatch.setattr(dc, "_output_dir", lambda: tmp_path)
    with patch("domain_checker.check_domains", return_value=["myapp.io"]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 0
    assert (tmp_path / "myapp.csv").exists()
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_domain_checker.py::test_main_no_args_exits_2 tests/test_domain_checker.py::test_main_no_available_domains_exits_1 tests/test_domain_checker.py::test_main_writes_file_when_available -v
```

Expected: 3 FAILED with `NotImplementedError`

- [ ] **Step 3: Implement `main()`**

Replace the `main` stub:
```python
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
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests PASSED (includes existing dnsexists tests)

---

### Task 6: Manual CLI verification

**Files:** (no changes)

- [ ] **Step 1: Run with a real name**

```bash
python domain_checker.py myapp
```

Expected: either `Results written to ...output/myapp.csv` (exit 0) or `No domains available for myapp` (exit 1).

- [ ] **Step 2: If a CSV was written, inspect it**

```bash
cat output/myapp.csv
```

Expected: header `domain,tld,available` followed by 20 rows, one per TLD.

- [ ] **Step 3: Run with no args**

```bash
python domain_checker.py
```

Expected: `Usage: python domain_checker.py <name>`, exit 2.

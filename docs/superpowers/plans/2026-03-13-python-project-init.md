# Python Project Init Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize `dnsexists` as a minimal Python 3.12 CLI tool that checks whether a DNS name exists.

**Architecture:** Single-module flat layout — `dnsexists.py` holds all logic and the `main()` CLI entry point. DNS resolution uses Python's stdlib `socket` module. Tests live in `tests/test_dnsexists.py` and run via `pytest`.

**Tech Stack:** Python 3.12, `socket` (stdlib), `pytest`

> **Note:** All git operations (commit, push) are handled by the user. Do NOT run `git commit` or `git push`.

---

## Chunk 1: Project Scaffolding

### Task 1: Create requirements files

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`

- [ ] **Step 1: Create `requirements.txt`** (empty — no runtime deps needed)

```
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
pytest>=8.0
```

---

### Task 2: Bootstrap test file and `dnsexists.py`

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_dnsexists.py`
- Create: `dnsexists.py`

> **Network note:** Tests make live DNS calls. They require network access and will fail in isolated CI environments. This is acceptable for a local CLI tool; mark tests with `@pytest.mark.network` if CI isolation is needed in the future.

- [ ] **Step 1: Create `tests/` directory and empty `tests/__init__.py`**

Create an empty file at `tests/__init__.py`.

- [ ] **Step 2: Write the failing test**

`tests/test_dnsexists.py`:
```python
import pytest
from dnsexists import resolve


def test_resolve_returns_true_for_known_host():
    assert resolve("dns.google") is True


def test_resolve_returns_false_for_nonexistent_host():
    assert resolve("this-host-does-not-exist.invalid") is False
```

- [ ] **Step 3: Run test to verify it fails (import error)**

```bash
pytest tests/test_dnsexists.py -v
```

Expected: `ImportError: cannot import name 'resolve' from 'dnsexists'` (or `ModuleNotFoundError`)

- [ ] **Step 4: Create `dnsexists.py` with stub `resolve()`**

```python
import socket
import sys


def resolve(hostname: str) -> bool:
    raise NotImplementedError


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python dnsexists.py <hostname>")
        sys.exit(1)
    hostname = sys.argv[1]
    if resolve(hostname):
        print(f"{hostname}: EXISTS")
        sys.exit(0)
    else:
        print(f"{hostname}: NOT FOUND")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they fail (not pass)**

```bash
pytest tests/test_dnsexists.py -v
```

Expected: 2 FAILED with `NotImplementedError`

- [ ] **Step 6: Implement `resolve()`**

Replace the `resolve` stub in `dnsexists.py`:

```python
def resolve(hostname: str) -> bool:
    """Return True if hostname resolves in DNS, False otherwise."""
    try:
        socket.getaddrinfo(hostname, None)
        return True
    except socket.gaierror:
        return False
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/test_dnsexists.py -v
```

Expected: 2 PASSED

---

### Task 3: Test the CLI manually

**Files:** (no changes)

- [ ] **Step 1: Run against a known host**

```bash
python dnsexists.py dns.google
```

Expected output: `dns.google: EXISTS` (exit code 0)

- [ ] **Step 2: Run against a nonexistent host**

```bash
python dnsexists.py this-host-does-not-exist.invalid
```

Expected output: `this-host-does-not-exist.invalid: NOT FOUND` (exit code 1)

- [ ] **Step 3: Run with no arguments**

```bash
python dnsexists.py
```

Expected output: `Usage: python dnsexists.py <hostname>` (exit code 1)

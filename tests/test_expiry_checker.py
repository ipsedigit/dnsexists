import csv
import datetime
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

import expiry_checker


TODAY = datetime.date(2026, 3, 17)


def _write_input(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["domain", "expiration_date", "notes"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _read_input(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _read_output(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _run(tmp_path, rows, today=TODAY):
    input_path = tmp_path / "expiry" / "domains.csv"
    _write_input(input_path, rows)
    expiry_checker.run(input_path=input_path, today=today)
    out_dir = tmp_path / "expiry" / "output"
    files = list(out_dir.glob("*-expiring.csv"))
    assert len(files) == 1
    return _read_output(files[0]), input_path


# --- missing input file ---

def test_missing_input_file_exits_1_with_stderr(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        expiry_checker.run(input_path=tmp_path / "expiry" / "domains.csv", today=TODAY)
    assert exc.value.code == 1
    assert capsys.readouterr().err != ""


# --- reads input CSV correctly ---

def test_reads_known_expiry_date_without_whois(tmp_path):
    rows = [{"domain": "example.com", "expiration_date": "2026-04-10", "notes": "main site"}]
    with patch("expiry_checker.whois_client.expiry_date") as mock_whois:
        result, _ = _run(tmp_path, rows)
    mock_whois.assert_not_called()
    assert result[0]["domain"] == "example.com"


# --- skips WHOIS when expiration_date already present ---

def test_skips_whois_when_expiry_date_present(tmp_path):
    rows = [{"domain": "example.com", "expiration_date": "2026-03-20", "notes": ""}]
    with patch("expiry_checker.whois_client.expiry_date") as mock_whois:
        _run(tmp_path, rows)
    mock_whois.assert_not_called()


# --- backfills via WHOIS and writes back atomically ---

def test_backfills_expiry_date_from_whois(tmp_path):
    rows = [{"domain": "myproject.io", "expiration_date": "", "notes": "test"}]
    fetched = datetime.date(2026, 3, 30)
    with patch("expiry_checker.whois_client.expiry_date", return_value=fetched):
        _, input_path = _run(tmp_path, rows)
    written = _read_input(input_path)
    assert written[0]["expiration_date"] == "2026-03-30"


# --- failed WHOIS lookup leaves expiration_date blank ---

def test_failed_whois_leaves_expiry_blank(tmp_path, capsys):
    rows = [{"domain": "myproject.io", "expiration_date": "", "notes": ""}]
    with patch("expiry_checker.whois_client.expiry_date", return_value=None):
        _, input_path = _run(tmp_path, rows)
    written = _read_input(input_path)
    assert written[0]["expiration_date"] == ""
    assert "myproject.io" in capsys.readouterr().err


# --- filtering ---

def test_filters_out_domains_with_days_remaining_over_30(tmp_path):
    rows = [
        {"domain": "soon.com", "expiration_date": "2026-03-20", "notes": ""},   # 3 days
        {"domain": "far.com", "expiration_date": "2026-05-01", "notes": ""},    # 45 days
    ]
    result, _ = _run(tmp_path, rows)
    domains = [r["domain"] for r in result]
    assert "soon.com" in domains
    assert "far.com" not in domains


def test_includes_already_expired_domains(tmp_path):
    rows = [{"domain": "expired.com", "expiration_date": "2026-03-10", "notes": ""}]
    result, _ = _run(tmp_path, rows)
    assert result[0]["domain"] == "expired.com"
    assert int(result[0]["days_remaining"]) < 0


# --- sorting ---

def test_output_sorted_ascending_by_days_remaining(tmp_path):
    rows = [
        {"domain": "mid.com", "expiration_date": "2026-03-25", "notes": ""},   # 8 days
        {"domain": "expired.com", "expiration_date": "2026-03-10", "notes": ""},  # -7 days
        {"domain": "soon.com", "expiration_date": "2026-03-20", "notes": ""},   # 3 days
    ]
    result, _ = _run(tmp_path, rows)
    days = [int(r["days_remaining"]) for r in result]
    assert days == sorted(days)


# --- output directory created if missing ---

def test_output_directory_created_if_missing(tmp_path):
    rows = [{"domain": "example.com", "expiration_date": "2026-03-20", "notes": ""}]
    _run(tmp_path, rows)
    assert (tmp_path / "expiry" / "output").is_dir()


# --- deduplication ---

def test_duplicate_domains_uses_first_occurrence(tmp_path, capsys):
    rows = [
        {"domain": "example.com", "expiration_date": "2026-03-20", "notes": "first"},
        {"domain": "example.com", "expiration_date": "2026-03-25", "notes": "second"},
    ]
    result, _ = _run(tmp_path, rows)
    domains = [r["domain"] for r in result]
    assert domains.count("example.com") == 1
    assert result[0]["notes"] == "first"


def test_duplicate_domains_prints_warning(tmp_path, capsys):
    rows = [
        {"domain": "example.com", "expiration_date": "2026-03-20", "notes": ""},
        {"domain": "example.com", "expiration_date": "2026-03-25", "notes": ""},
    ]
    _run(tmp_path, rows)
    assert "example.com" in capsys.readouterr().err

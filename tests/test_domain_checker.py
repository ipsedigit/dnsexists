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


from domain_checker import check_domains


def test_check_domains_returns_available_domains():
    tlds = [".com", ".io", ".org"]
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

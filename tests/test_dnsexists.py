import logging
from unittest.mock import patch, call
import pytest
from dnsexists import is_available, check_domains, write_results, main
import csv as csv_module


# --- is_available ---

def test_is_available_returns_true_when_not_registered():
    with patch("dnsexists.whois_client.is_registered", return_value=False):
        assert is_available("example.com") is True


def test_is_available_returns_false_when_registered():
    with patch("dnsexists.whois_client.is_registered", return_value=True):
        assert is_available("google.com") is False


# --- check_domains ---

def test_check_domains_returns_available_domains():
    tlds = [".com", ".io", ".org"]
    availability = {
        "myapp.com": False,
        "myapp.io": True,
        "myapp.org": False,
    }
    with patch("dnsexists.is_available", side_effect=lambda d: availability[d]):
        result = check_domains("myapp", tlds, delay=0)
    assert result == ["myapp.io"]


def test_check_domains_returns_empty_when_all_taken():
    tlds = [".com", ".io"]
    with patch("dnsexists.is_available", return_value=False):
        result = check_domains("myapp", tlds, delay=0)
    assert result == []


def test_check_domains_sleeps_between_calls():
    tlds = [".com", ".io", ".org"]
    with patch("dnsexists.is_available", return_value=False):
        with patch("dnsexists.time.sleep") as mock_sleep:
            check_domains("myapp", tlds, delay=0.5)
    assert mock_sleep.call_count == 3
    mock_sleep.assert_called_with(0.5)


def test_check_domains_default_delay_is_one_second():
    import inspect
    sig = inspect.signature(check_domains)
    assert sig.parameters["delay"].default == 1.0


# --- logging ---

def test_check_domains_logs_each_domain_being_checked(caplog):
    with patch("dnsexists.is_available", return_value=False):
        with caplog.at_level(logging.INFO, logger="dnsexists"):
            check_domains("myapp", [".com", ".io"], delay=0)
    messages = [r.message for r in caplog.records]
    assert "Checking myapp.com..." in messages
    assert "Checking myapp.io..." in messages


def test_check_domains_logs_available_result(caplog):
    with patch("dnsexists.is_available", return_value=True):
        with caplog.at_level(logging.INFO, logger="dnsexists"):
            check_domains("myapp", [".com"], delay=0)
    messages = [r.message for r in caplog.records]
    assert "myapp.com: available" in messages


def test_check_domains_logs_taken_result(caplog):
    with patch("dnsexists.is_available", return_value=False):
        with caplog.at_level(logging.INFO, logger="dnsexists"):
            check_domains("myapp", [".com"], delay=0)
    messages = [r.message for r in caplog.records]
    assert "myapp.com: taken" in messages


# --- write_results ---

def test_write_results_uses_out_dir_when_provided(tmp_path):
    from dnsexists import write_results
    tlds = [".com", ".io"]
    path = write_results("myapp", ["myapp.io"], tlds, out_dir=tmp_path)
    assert path == tmp_path / "myapp.csv"
    assert path.exists()


def test_write_results_creates_nested_out_dir(tmp_path):
    from dnsexists import write_results
    nested = tmp_path / "dev" / "output"
    write_results("myapp", [], [".com"], out_dir=nested)
    assert nested.exists()

def test_write_results_creates_csv(tmp_path, monkeypatch):
    import dnsexists
    monkeypatch.setattr(dnsexists, "_output_dir", lambda: tmp_path)
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


# --- main ---

def test_main_no_args_exits_2(monkeypatch):
    monkeypatch.setattr("sys.argv", ["dnsexists.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_main_name_no_available_domains_exits_1(monkeypatch):
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--name", "myapp"])
    with patch("dnsexists.check_domains", return_value=[]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1


def test_main_name_writes_to_output(monkeypatch, tmp_path):
    import dnsexists as dc
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--name", "myapp"])
    monkeypatch.setattr(dc, "_root", lambda: tmp_path)
    with patch("dnsexists.check_domains", return_value=["myapp.io"]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 0
    assert (tmp_path / "output" / "myapp.csv").exists()


def test_main_unsupported_field_exits_2(monkeypatch):
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--field", "doesnotexist"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2

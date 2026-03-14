import logging
from unittest.mock import patch, call, MagicMock
import pytest
from dnsexists import is_available, check_domains, write_results, synthesize, main
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
    assert len(rows) == 1
    assert rows[0] == {"domain": "myapp.io", "tld": ".io"}
    assert "available" not in rows[0]


# --- synthesize ---

def test_synthesize_writes_top_10(tmp_path):
    scored = [(float(i), f"domain{i}.com") for i in range(15, 0, -1)]
    synthesize(scored, out_dir=tmp_path)
    with open(tmp_path / "insight.csv") as f:
        rows = list(csv_module.DictReader(f))
    assert len(rows) == 10


def test_synthesize_writes_all_when_fewer_than_10(tmp_path):
    scored = [(5.0, "a.com"), (3.0, "b.com"), (1.0, "c.com")]
    synthesize(scored, out_dir=tmp_path)
    with open(tmp_path / "insight.csv") as f:
        rows = list(csv_module.DictReader(f))
    assert len(rows) == 3


def test_synthesize_sorts_by_score_descending(tmp_path):
    scored = [(1.0, "low.com"), (100.0, "high.com"), (50.0, "mid.com")]
    synthesize(scored, out_dir=tmp_path)
    with open(tmp_path / "insight.csv") as f:
        rows = list(csv_module.DictReader(f))
    assert rows[0]["domain"] == "high.com"
    assert rows[1]["domain"] == "mid.com"
    assert rows[2]["domain"] == "low.com"


def test_synthesize_breaks_ties_by_domain_ascending(tmp_path):
    scored = [(10.0, "zzz.com"), (10.0, "aaa.com"), (10.0, "mmm.com")]
    synthesize(scored, out_dir=tmp_path)
    with open(tmp_path / "insight.csv") as f:
        rows = list(csv_module.DictReader(f))
    assert rows[0]["domain"] == "aaa.com"
    assert rows[1]["domain"] == "mmm.com"
    assert rows[2]["domain"] == "zzz.com"


def test_synthesize_csv_has_only_domain_and_score_columns(tmp_path):
    scored = [(5.0, "example.com")]
    synthesize(scored, out_dir=tmp_path)
    with open(tmp_path / "insight.csv") as f:
        reader = csv_module.DictReader(f)
        assert set(reader.fieldnames) == {"domain", "score"}


def test_synthesize_empty_input_writes_header_only(tmp_path):
    synthesize([], out_dir=tmp_path)
    with open(tmp_path / "insight.csv") as f:
        rows = list(csv_module.DictReader(f))
    assert rows == []
    assert (tmp_path / "insight.csv").exists()


def test_synthesize_creates_out_dir(tmp_path):
    nested = tmp_path / "insight"
    synthesize([], out_dir=nested)
    assert nested.exists()
    assert (nested / "insight.csv").exists()


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


def test_main_no_args_usage_contains_limit(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["dnsexists.py"])
    with pytest.raises(SystemExit):
        main()
    out = capsys.readouterr().out
    assert "[--limit N]" in out


def _make_field_mock(n=5):
    candidates = [{"name": f"name{i}", "score": float(n - i), "sources": ["github"]} for i in range(n)]
    names = [c["name"] for c in candidates]
    mod = MagicMock()
    mod.fetch.return_value = candidates
    mod.select.return_value = names
    return mod


def test_main_limit_caps_check_domains_calls(monkeypatch, tmp_path):
    import dnsexists as dc
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--field", "dev", "--limit", "2"])
    monkeypatch.setattr(dc, "_root", lambda: tmp_path)
    with patch("dnsexists.importlib.import_module", return_value=_make_field_mock(5)), \
         patch("dnsexists.check_domains", return_value=[]) as mock_check, \
         patch("dnsexists.write_results"), \
         patch("dnsexists.synthesize"):
        with pytest.raises(SystemExit):
            main()
    assert mock_check.call_count == 2


def test_main_limit_greater_than_names_checks_all(monkeypatch, tmp_path):
    import dnsexists as dc
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--field", "dev", "--limit", "10"])
    monkeypatch.setattr(dc, "_root", lambda: tmp_path)
    with patch("dnsexists.importlib.import_module", return_value=_make_field_mock(5)), \
         patch("dnsexists.check_domains", return_value=[]) as mock_check, \
         patch("dnsexists.write_results"), \
         patch("dnsexists.synthesize"):
        with pytest.raises(SystemExit):
            main()
    assert mock_check.call_count == 5


def test_main_limit_absent_checks_all(monkeypatch, tmp_path):
    import dnsexists as dc
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--field", "dev"])
    monkeypatch.setattr(dc, "_root", lambda: tmp_path)
    with patch("dnsexists.importlib.import_module", return_value=_make_field_mock(5)), \
         patch("dnsexists.check_domains", return_value=[]) as mock_check, \
         patch("dnsexists.write_results"), \
         patch("dnsexists.synthesize"):
        with pytest.raises(SystemExit):
            main()
    assert mock_check.call_count == 5


def test_main_limit_non_integer_exits_2(monkeypatch):
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--field", "dev", "--limit", "abc"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_main_limit_zero_exits_2(monkeypatch):
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--field", "dev", "--limit", "0"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_main_field_calls_synthesize_with_scored_domains(monkeypatch, tmp_path):
    import dnsexists
    monkeypatch.setattr("sys.argv", ["dnsexists.py", "--field", "dev"])
    monkeypatch.setattr(dnsexists, "_root", lambda: tmp_path)

    candidates = [
        {"name": "alpha", "score": 10.0, "sources": ["github"]},
        {"name": "beta", "score": 5.0, "sources": ["hn"]},
    ]

    def mock_check(name, tlds, delay=1.0):
        return [f"{name}.com"]

    with patch("dnsexists.importlib.import_module") as mock_import, \
         patch("dnsexists.check_domains", side_effect=mock_check), \
         patch("dnsexists.write_results"), \
         patch("dnsexists.synthesize") as mock_synthesize:

        mock_mod = MagicMock()
        mock_mod.fetch.return_value = candidates
        mock_mod.select.return_value = ["alpha", "beta"]
        mock_import.return_value = mock_mod

        with pytest.raises(SystemExit):
            main()

    mock_synthesize.assert_called_once_with(
        [(10.0, "alpha.com"), (5.0, "beta.com")],
        out_dir=tmp_path / "dev" / "output" / "insight",
    )

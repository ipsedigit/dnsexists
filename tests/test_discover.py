import csv
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

import dnsexists


class TestFieldPipelineUnknownField:
    def test_unknown_field_exits_2(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["dnsexists.py", "--field", "doesnotexist"])
        with pytest.raises(SystemExit) as exc:
            dnsexists.main()
        assert exc.value.code == 2

    def test_unknown_field_prints_error(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["dnsexists.py", "--field", "doesnotexist"])
        with pytest.raises(SystemExit):
            dnsexists.main()
        assert "Unknown field: doesnotexist" in capsys.readouterr().out


class TestFieldPipelineEmptyFetch:
    def test_empty_fetch_writes_header_only_csv(self, monkeypatch, tmp_path):
        field_mod = MagicMock()
        field_mod.fetch.return_value = []
        monkeypatch.setattr(sys, "argv", ["dnsexists.py", "--field", "dev"])
        monkeypatch.setattr(dnsexists, "_root", lambda: tmp_path)
        with patch("importlib.import_module", return_value=field_mod):
            with pytest.raises(SystemExit) as exc:
                dnsexists.main()

        assert exc.value.code == 0
        csv_path = tmp_path / "dev" / "input" / "candidates.csv"
        assert csv_path.exists()
        assert csv_path.read_text().strip() == "name"
        field_mod.select.assert_not_called()

    def test_empty_fetch_logs_warning(self, monkeypatch, tmp_path, caplog):
        import logging
        field_mod = MagicMock()
        field_mod.fetch.return_value = []
        monkeypatch.setattr(sys, "argv", ["dnsexists.py", "--field", "dev"])
        monkeypatch.setattr(dnsexists, "_root", lambda: tmp_path)
        with patch("importlib.import_module", return_value=field_mod):
            with caplog.at_level(logging.WARNING, logger="dnsexists"):
                with pytest.raises(SystemExit):
                    dnsexists.main()
        assert any("dev.fetch" in r.message for r in caplog.records)


class TestFieldPipelineEmptySelect:
    def test_empty_select_does_not_call_check_domains(self, monkeypatch, tmp_path):
        field_mod = MagicMock()
        field_mod.fetch.return_value = [{"name": "myrepo"}]
        field_mod.select.return_value = []
        monkeypatch.setattr(sys, "argv", ["dnsexists.py", "--field", "dev"])
        monkeypatch.setattr(dnsexists, "_root", lambda: tmp_path)
        with patch("importlib.import_module", return_value=field_mod):
            with patch("dnsexists.check_domains") as mock_check:
                with pytest.raises(SystemExit) as exc:
                    dnsexists.main()

        assert exc.value.code == 0
        mock_check.assert_not_called()


class TestFieldPipelineHappyPath:
    def test_input_csv_written_with_correct_headers_and_rows(self, monkeypatch, tmp_path):
        field_mod = MagicMock()
        field_mod.fetch.return_value = [
            {"name": "myrepo", "score": 100.0, "sources": ["github"]},
            {"name": "cooltool", "score": 200.0, "sources": ["github"]},
        ]
        field_mod.select.return_value = ["myrepo", "cooltool"]
        monkeypatch.setattr(sys, "argv", ["dnsexists.py", "--field", "dev"])
        monkeypatch.setattr(dnsexists, "_root", lambda: tmp_path)
        with patch("importlib.import_module", return_value=field_mod):
            with patch("dnsexists.check_domains", return_value=[]):
                with patch("dnsexists.write_results"):
                    with pytest.raises(SystemExit):
                        dnsexists.main()

        csv_path = tmp_path / "dev" / "input" / "candidates.csv"
        assert csv_path.exists()
        with open(csv_path) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert list(rows[0].keys())[0] == "name"
        assert rows[0]["name"] == "myrepo"
        assert rows[1]["name"] == "cooltool"

    def test_write_results_called_with_correct_out_dir(self, monkeypatch, tmp_path):
        field_mod = MagicMock()
        field_mod.fetch.return_value = [{"name": "myrepo", "score": 1.0, "sources": ["github"]}]
        field_mod.select.return_value = ["myrepo"]
        monkeypatch.setattr(sys, "argv", ["dnsexists.py", "--field", "dev"])
        monkeypatch.setattr(dnsexists, "_root", lambda: tmp_path)
        with patch("importlib.import_module", return_value=field_mod):
            with patch("dnsexists.check_domains", return_value=[]):
                with patch("dnsexists.write_results") as mock_write:
                    with pytest.raises(SystemExit):
                        dnsexists.main()

        _, kwargs = mock_write.call_args
        assert kwargs.get("out_dir") == tmp_path / "dev" / "output"

    def test_check_domains_called_once_per_name(self, monkeypatch, tmp_path):
        field_mod = MagicMock()
        field_mod.fetch.return_value = [{"name": "myrepo", "score": 1.0, "sources": ["github"]}, {"name": "cooltool", "score": 2.0, "sources": ["github"]}]
        field_mod.select.return_value = ["myrepo", "cooltool"]
        monkeypatch.setattr(sys, "argv", ["dnsexists.py", "--field", "dev"])
        monkeypatch.setattr(dnsexists, "_root", lambda: tmp_path)
        with patch("importlib.import_module", return_value=field_mod):
            with patch("dnsexists.check_domains", return_value=[]) as mock_check:
                with patch("dnsexists.write_results"):
                    with pytest.raises(SystemExit):
                        dnsexists.main()

        assert mock_check.call_count == 2

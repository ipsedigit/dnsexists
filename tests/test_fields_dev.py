import os
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fields.dev import fetch, select


def _mock_response(items, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"items": items}
    resp.text = "error message"
    return resp


def _make_item(name="myrepo", stars=1000, url="https://github.com/u/myrepo",
               created_at="2026-02-01T00:00:00Z", description="A cool repo"):
    return {
        "name": name,
        "stargazers_count": stars,
        "html_url": url,
        "created_at": created_at,
        "description": description,
    }


class TestFetch:
    def test_returns_correct_fields(self):
        items = [_make_item("myrepo", 1000, "https://github.com/u/myrepo",
                            "2026-02-01T00:00:00Z", "cool")]
        with patch("requests.get", return_value=_mock_response(items)):
            result = fetch({})
        assert len(result) == 1
        assert result[0]["name"] == "myrepo"
        assert result[0]["stars"] == 1000
        assert result[0]["url"] == "https://github.com/u/myrepo"
        assert result[0]["created_at"] == "2026-02-01T00:00:00Z"
        assert result[0]["description"] == "cool"

    def test_name_is_first_key(self):
        items = [_make_item()]
        with patch("requests.get", return_value=_mock_response(items)):
            result = fetch({})
        assert list(result[0].keys())[0] == "name"

    def test_uses_created_filter_in_query(self):
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            fetch({})
        params = mock_get.call_args[1]["params"]
        assert "created:>" in params["q"]
        assert params["sort"] == "stars"
        assert params["order"] == "desc"

    def test_query_cutoff_respects_days_param(self):
        expected_cutoff = (date.today() - timedelta(days=7)).isoformat()
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            fetch({"days": 7})
        params = mock_get.call_args[1]["params"]
        assert expected_cutoff in params["q"]

    def test_query_uses_default_30_days(self):
        expected_cutoff = (date.today() - timedelta(days=30)).isoformat()
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            fetch({})
        params = mock_get.call_args[1]["params"]
        assert expected_cutoff in params["q"]

    def test_limit_param_sets_per_page(self):
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            fetch({"limit": 10})
        params = mock_get.call_args[1]["params"]
        assert params["per_page"] == 10

    def test_default_limit_is_50(self):
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            fetch({})
        params = mock_get.call_args[1]["params"]
        assert params["per_page"] == 50

    def test_sends_auth_header_when_token_set(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "mytoken")
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            fetch({})
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Authorization") == "Bearer mytoken"

    def test_omits_auth_header_when_token_absent(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            fetch({})
        headers = mock_get.call_args[1]["headers"]
        assert "Authorization" not in headers

    def test_raises_runtime_error_on_non_200(self):
        with patch("requests.get", return_value=_mock_response([], status_code=403)):
            with pytest.raises(RuntimeError, match="403"):
                fetch({})

    def test_null_description_becomes_empty_string(self):
        item = _make_item()
        item["description"] = None
        with patch("requests.get", return_value=_mock_response([item])):
            result = fetch({})
        assert result[0]["description"] == ""


class TestSelect:
    def test_returns_all_valid_names(self):
        candidates = [{"name": "myrepo"}, {"name": "cooltool"}]
        assert select(candidates) == ["myrepo", "cooltool"]

    def test_strips_invalid_characters(self):
        assert select([{"name": "my repo!"}]) == ["my-repo"]

    def test_lowercases_names(self):
        assert select([{"name": "MyRepo"}]) == ["myrepo"]

    def test_removes_leading_hyphens(self):
        assert select([{"name": "--myrepo"}]) == ["myrepo"]

    def test_removes_trailing_hyphens(self):
        assert select([{"name": "myrepo--"}]) == ["myrepo"]

    def test_drops_empty_results(self):
        assert select([{"name": "!!!"}]) == []

    def test_drops_empty_string_name(self):
        assert select([{"name": ""}]) == []

    def test_drops_names_shorter_than_3_chars(self):
        assert select([{"name": "ab"}]) == []

    def test_keeps_names_exactly_3_chars(self):
        assert select([{"name": "abc"}]) == ["abc"]

    def test_drops_names_longer_than_30_chars(self):
        assert select([{"name": "a" * 31}]) == []

    def test_keeps_names_exactly_30_chars(self):
        assert select([{"name": "a" * 30}]) == ["a" * 30]

    def test_drops_all_digit_names(self):
        assert select([{"name": "12345"}]) == []

    def test_keeps_names_with_mixed_digits(self):
        assert select([{"name": "repo123"}]) == ["repo123"]

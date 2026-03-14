import os
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fields.dev import fetch, select, _fetch_github, _fetch_hn, _fetch_reddit, _fetch_ph, _merge, _extract_tokens, _sample


# ── helpers ──────────────────────────────────────────────────────────────────

def _gh_response(items, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"items": items}
    return resp


def _gh_item(name="myrepo", stars=100, created_at=None):
    created_at = created_at or date.today().isoformat() + "T00:00:00Z"
    return {"name": name, "stargazers_count": stars, "created_at": created_at}


def _hn_response(hits, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"hits": hits}
    return resp


def _hn_hit(title="myproject", points=500):
    return {"title": title, "points": points}


def _reddit_response(children, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"data": {"children": [{"data": c} for c in children]}}
    return resp


def _ph_response(nodes, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"data": {"posts": {"edges": [{"node": n} for n in nodes]}}}
    return resp


# ── _fetch_github ─────────────────────────────────────────────────────────────

class TestFetchGitHub:
    def test_returns_name_score_source(self):
        items = [_gh_item("myrepo", stars=100)]
        with patch("requests.get", return_value=_gh_response(items)):
            result = _fetch_github(days=7, limit=50)
        assert len(result) == 1
        assert result[0]["name"] == "myrepo"
        assert result[0]["score"] == pytest.approx(100.0)
        assert result[0]["source"] == "github"

    def test_score_is_stars_divided_by_age_days(self):
        created = (date.today() - timedelta(days=2)).isoformat() + "T00:00:00Z"
        items = [_gh_item("myrepo", stars=200, created_at=created)]
        with patch("requests.get", return_value=_gh_response(items)):
            result = _fetch_github(days=7, limit=50)
        assert result[0]["score"] == pytest.approx(100.0)  # 200 / 2

    def test_excludes_repos_older_than_days(self):
        old = (date.today() - timedelta(days=10)).isoformat() + "T00:00:00Z"
        items = [_gh_item("oldrepo", stars=1000, created_at=old)]
        with patch("requests.get", return_value=_gh_response(items)):
            result = _fetch_github(days=7, limit=50)
        assert result == []

    def test_returns_empty_on_non_200(self):
        with patch("requests.get", return_value=_gh_response([], status=403)):
            result = _fetch_github(days=7, limit=50)
        assert result == []

    def test_returns_empty_on_network_error(self):
        with patch("requests.get", side_effect=ConnectionError("fail")):
            result = _fetch_github(days=7, limit=50)
        assert result == []

    def test_uses_token_when_set(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "mytoken")
        with patch("requests.get", return_value=_gh_response([])) as mock_get:
            _fetch_github(days=7, limit=50)
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Authorization") == "Bearer mytoken"

    def test_omits_auth_when_token_absent(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with patch("requests.get", return_value=_gh_response([])) as mock_get:
            _fetch_github(days=7, limit=50)
        headers = mock_get.call_args[1]["headers"]
        assert "Authorization" not in headers

    def test_uses_10_second_timeout(self):
        with patch("requests.get", return_value=_gh_response([])) as mock_get:
            _fetch_github(days=7, limit=50)
        assert mock_get.call_args[1]["timeout"] == 10


# ── _fetch_hn ─────────────────────────────────────────────────────────────────

class TestFetchHN:
    def test_returns_name_score_source(self):
        with patch("requests.get", return_value=_hn_response([_hn_hit("myproject", 500)])):
            result = _fetch_hn(days=7, limit=50)
        assert len(result) == 1
        assert result[0]["name"] == "myproject"
        assert result[0]["score"] == pytest.approx(500.0)
        assert result[0]["source"] == "hn"

    def test_returns_empty_on_non_200(self):
        with patch("requests.get", return_value=_hn_response([], status=500)):
            result = _fetch_hn(days=7, limit=50)
        assert result == []

    def test_returns_empty_on_network_error(self):
        with patch("requests.get", side_effect=ConnectionError("fail")):
            result = _fetch_hn(days=7, limit=50)
        assert result == []

    def test_uses_10_second_timeout(self):
        with patch("requests.get", return_value=_hn_response([])) as mock_get:
            _fetch_hn(days=7, limit=50)
        assert mock_get.call_args[1]["timeout"] == 10

    def test_extracts_tokens_not_full_title(self):
        hit = _hn_hit("Tony Hoare has died", points=500)
        with patch("requests.get", return_value=_hn_response([hit])):
            result = _fetch_hn(days=7, limit=50)
        names = [r["name"] for r in result]
        assert "tony" in names
        assert "hoare" in names
        assert "died" in names
        assert "has" not in names
        assert not any(" " in n for n in names)

    def test_skips_story_when_all_tokens_filtered(self):
        hit = _hn_hit("the and for", points=500)
        with patch("requests.get", return_value=_hn_response([hit])):
            result = _fetch_hn(days=7, limit=50)
        assert result == []

    def test_score_divided_equally_among_tokens(self):
        hit = _hn_hit("Tony Hoare died", points=300)  # 3 valid tokens
        with patch("requests.get", return_value=_hn_response([hit])):
            result = _fetch_hn(days=7, limit=50)
        assert all(r["score"] == pytest.approx(100.0) for r in result)


# ── _fetch_reddit ─────────────────────────────────────────────────────────────

class TestFetchReddit:
    def test_returns_name_score_source(self):
        children = [{"title": "myproject", "score": 300}]
        with patch("requests.get", return_value=_reddit_response(children)):
            result = _fetch_reddit(days=7, limit=50)
        assert any(r["name"] == "myproject" for r in result)
        assert all(r["source"] == "reddit" for r in result)

    def test_sets_user_agent_header(self):
        with patch("requests.get", return_value=_reddit_response([])) as mock_get:
            _fetch_reddit(days=7, limit=50)
        for call_args in mock_get.call_args_list:
            assert "User-Agent" in call_args[1]["headers"]

    def test_returns_empty_when_all_subreddits_fail(self):
        resp = MagicMock()
        resp.status_code = 429
        with patch("requests.get", return_value=resp):
            result = _fetch_reddit(days=7, limit=50)
        assert result == []

    def test_returns_empty_on_network_error(self):
        with patch("requests.get", side_effect=ConnectionError("fail")):
            result = _fetch_reddit(days=7, limit=50)
        assert result == []

    def test_uses_10_second_timeout(self):
        with patch("requests.get", return_value=_reddit_response([])) as mock_get:
            _fetch_reddit(days=7, limit=50)
        for call_args in mock_get.call_args_list:
            assert call_args[1]["timeout"] == 10

    def test_extracts_tokens_not_full_title(self):
        children = [{"title": "Tony Hoare has died", "score": 300}]
        with patch("requests.get", return_value=_reddit_response(children)):
            result = _fetch_reddit(days=7, limit=50)
        names = [r["name"] for r in result]
        assert "tony" in names
        assert "hoare" in names
        assert "died" in names
        assert "has" not in names
        assert not any(" " in n for n in names)

    def test_skips_post_when_all_tokens_filtered(self):
        children = [{"title": "the and for", "score": 300}]
        with patch("requests.get", return_value=_reddit_response(children)):
            result = _fetch_reddit(days=7, limit=50)
        assert result == []

    def test_score_divided_equally_among_tokens(self):
        children = [{"title": "Tony Hoare died", "score": 300}]  # 3 valid tokens
        with patch("requests.get", return_value=_reddit_response(children)):
            result = _fetch_reddit(days=7, limit=50)
        assert all(r["score"] == pytest.approx(100.0) for r in result)


# ── _fetch_ph ─────────────────────────────────────────────────────────────────

class TestFetchPH:
    def test_returns_empty_when_token_absent(self, monkeypatch):
        monkeypatch.delenv("PRODUCT_HUNT_TOKEN", raising=False)
        result = _fetch_ph(days=7, limit=50)
        assert result == []

    def test_returns_name_score_source(self, monkeypatch):
        monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "tok")
        nodes = [{"name": "MyCoolApp", "votesCount": 200}]
        with patch("requests.post", return_value=_ph_response(nodes)):
            result = _fetch_ph(days=7, limit=50)
        assert len(result) == 1
        assert result[0]["name"] == "MyCoolApp"
        assert result[0]["score"] == pytest.approx(200.0)
        assert result[0]["source"] == "producthunt"

    def test_returns_empty_on_non_200(self, monkeypatch):
        monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "tok")
        with patch("requests.post", return_value=_ph_response([], status=500)):
            result = _fetch_ph(days=7, limit=50)
        assert result == []

    def test_returns_empty_on_network_error(self, monkeypatch):
        monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "tok")
        with patch("requests.post", side_effect=ConnectionError("fail")):
            result = _fetch_ph(days=7, limit=50)
        assert result == []

    def test_uses_10_second_timeout(self, monkeypatch):
        monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "tok")
        with patch("requests.post", return_value=_ph_response([])) as mock_post:
            _fetch_ph(days=7, limit=50)
        assert mock_post.call_args[1]["timeout"] == 10


# ── _merge ────────────────────────────────────────────────────────────────────

class TestMerge:
    def test_deduplicates_by_normalized_name(self):
        entries = [
            {"name": "My_Tool", "score": 10, "source": "github"},
            {"name": "my-tool", "score": 5, "source": "hn"},
        ]
        result = _merge(entries, weights={"github": 1.0, "hn": 0.8})
        assert len(result) == 1
        assert result[0]["name"] == "my-tool"

    def test_sums_weighted_scores(self):
        entries = [
            {"name": "mytool", "score": 10, "source": "github"},
            {"name": "mytool", "score": 50, "source": "hn"},
        ]
        result = _merge(entries, weights={"github": 1.0, "hn": 0.8})
        # weighted sum = 10*1.0 + 50*0.8 = 50.0, multiplier = 2 → 100.0
        assert result[0]["score"] == pytest.approx(100.0)

    def test_cross_source_multiplier_boosts_multi_source_names(self):
        single = [{"name": "tool", "score": 100, "source": "github"}]
        multi = [
            {"name": "tool", "score": 50, "source": "github"},
            {"name": "tool", "score": 50, "source": "hn"},
        ]
        r_single = _merge(single, weights={"github": 1.0, "hn": 0.8})
        r_multi = _merge(multi, weights={"github": 1.0, "hn": 0.8})
        assert r_multi[0]["score"] > r_single[0]["score"]

    def test_stores_sources_list(self):
        entries = [
            {"name": "mytool", "score": 10, "source": "github"},
            {"name": "mytool", "score": 20, "source": "hn"},
        ]
        result = _merge(entries, weights={"github": 1.0, "hn": 0.8})
        assert set(result[0]["sources"]) == {"github", "hn"}

    def test_sorts_by_score_descending(self):
        entries = [
            {"name": "low", "score": 1, "source": "github"},
            {"name": "high", "score": 100, "source": "github"},
            {"name": "mid", "score": 50, "source": "github"},
        ]
        result = _merge(entries, weights={"github": 1.0})
        assert result[0]["name"] == "high"
        assert result[1]["name"] == "mid"
        assert result[2]["name"] == "low"

    def test_merge_returns_all_entries(self):
        entries = [{"name": f"tool{i}", "score": float(i + 1), "source": "github"} for i in range(20)]
        result = _merge(entries, weights={"github": 1.0})
        assert len(result) == 20

    def test_returns_all_when_fewer_than_limit(self):
        entries = [{"name": "only", "score": 1.0, "source": "github"}]
        result = _merge(entries, weights={"github": 1.0})
        assert len(result) == 1


# ── fetch (integration) ───────────────────────────────────────────────────────

class TestFetch:
    def test_returns_merged_results_from_all_sources(self):
        gh = [{"name": "trending", "score": 100.0, "source": "github"}]
        hn = [{"name": "trending", "score": 200.0, "source": "hn"}]
        with patch("fields.dev._fetch_github", return_value=gh), \
             patch("fields.dev._fetch_hn", return_value=hn), \
             patch("fields.dev._fetch_reddit", return_value=[]), \
             patch("fields.dev._fetch_ph", return_value=[]), \
             patch("fields.dev._sample", side_effect=lambda c, l: c[:l]):
            result = fetch({})
        assert len(result) == 1
        assert result[0]["name"] == "trending"

    def test_default_days_is_7(self):
        with patch("fields.dev._fetch_github", return_value=[]) as mock_gh, \
             patch("fields.dev._fetch_hn", return_value=[]), \
             patch("fields.dev._fetch_reddit", return_value=[]), \
             patch("fields.dev._fetch_ph", return_value=[]):
            fetch({})
        mock_gh.assert_called_once_with(days=7, limit=50)

    def test_args_passed_to_fetchers(self):
        with patch("fields.dev._fetch_github", return_value=[]) as mock_gh, \
             patch("fields.dev._fetch_hn", return_value=[]), \
             patch("fields.dev._fetch_reddit", return_value=[]), \
             patch("fields.dev._fetch_ph", return_value=[]):
            fetch({"days": 3, "limit": 10})
        mock_gh.assert_called_once_with(days=3, limit=10)


# ── select ────────────────────────────────────────────────────────────────────

class TestSelect:
    def test_returns_all_valid_names(self):
        candidates = [{"name": "myrepo"}, {"name": "cooltool"}]
        assert select(candidates) == ["myrepo", "cooltool"]

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

    def test_drops_empty_name(self):
        assert select([{"name": ""}]) == []


# ── _extract_tokens ───────────────────────────────────────────────────────────

class TestExtractTokens:
    def test_returns_valid_words_lowercased(self):
        assert _extract_tokens("Tony Hoare died") == ["tony", "hoare", "died"]

    def test_excludes_stop_words(self):
        assert "has" not in _extract_tokens("Tony Hoare has died")

    def test_excludes_tokens_shorter_than_3_chars(self):
        assert _extract_tokens("Go is fast") == ["fast"]

    def test_keeps_token_exactly_3_chars(self):
        assert "cat" in _extract_tokens("cat sat mat")

    def test_excludes_tokens_longer_than_30_chars(self):
        long = "a" * 31
        assert _extract_tokens(f"hello {long}") == ["hello"]

    def test_excludes_all_digit_tokens(self):
        assert _extract_tokens("2024 release") == ["release"]

    def test_excludes_tokens_with_no_letters(self):
        assert _extract_tokens("1.0 launch") == ["launch"]

    def test_strips_punctuation_from_token_edges(self):
        result = _extract_tokens("rust! (fast)")
        assert "rust" in result
        assert "fast" in result

    def test_returns_empty_for_all_stop_words(self):
        assert _extract_tokens("the and for") == []

    def test_returns_empty_for_empty_string(self):
        assert _extract_tokens("") == []


# ── _sample ───────────────────────────────────────────────────────────────────

def _make_candidates(n=20):
    return [{"name": f"c{i}", "score": float(i)} for i in range(1, n + 1)]


class TestSample:
    def test_sample_returns_limit_items(self):
        candidates = _make_candidates(20)
        result = _sample(candidates, 5)
        assert len(result) == 5

    def test_sample_returns_all_when_fewer_than_limit(self):
        candidates = _make_candidates(3)
        result = _sample(candidates, 10)
        assert len(result) == 3

    def test_sample_excludes_zero_score_candidates(self):
        candidates = [
            {"name": "good", "score": 10.0},
            {"name": "zero", "score": 0.0},
            {"name": "alsogoood", "score": 5.0},
        ]
        for _ in range(20):
            result = _sample(candidates, 10)
            assert all(r["name"] != "zero" for r in result)

    def test_sample_is_non_deterministic(self):
        import random
        candidates = _make_candidates(20)
        random.seed(1)
        result_a = [r["name"] for r in _sample(candidates, 5)]
        random.seed(2)
        result_b = [r["name"] for r in _sample(candidates, 5)]
        assert result_a != result_b

    def test_sample_favors_higher_scored_candidates(self):
        import random
        candidates = _make_candidates(20)
        counts = {}
        random.seed(0)
        for _ in range(200):
            for r in _sample(candidates, 5):
                counts[r["name"]] = counts.get(r["name"], 0) + 1
        assert counts.get("c20", 0) > counts.get("c1", 0)

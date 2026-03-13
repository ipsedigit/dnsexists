import pytest
from fields.dev import fetch, select


class TestFetch:
    def test_returns_non_empty_list(self):
        result = fetch({})
        assert len(result) > 0

    def test_each_dict_has_name_stars_url(self):
        for item in fetch({}):
            assert "name" in item
            assert "stars" in item
            assert "url" in item

    def test_name_is_first_key(self):
        for item in fetch({}):
            assert list(item.keys())[0] == "name"

    def test_name_is_string(self):
        for item in fetch({}):
            assert isinstance(item["name"], str)

    def test_stars_is_int(self):
        for item in fetch({}):
            assert isinstance(item["stars"], int)


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

import csv
import io
import sys
from pathlib import Path

import pytest

import tranco_scorer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rows(*pairs):
    """Return list of (rank, domain) tuples."""
    return list(pairs)


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# filter_it
# ---------------------------------------------------------------------------

def test_filter_keeps_only_it_domains():
    rows = _make_rows(
        (1, "google.com"),
        (2, "repubblica.it"),
        (3, "amazon.co.uk"),
        (4, "corriere.it"),
    )
    result = tranco_scorer.filter_it(rows)
    assert [d for _, d in result] == ["repubblica.it", "corriere.it"]


def test_filter_returns_empty_when_no_it_domains():
    rows = _make_rows((1, "google.com"), (2, "amazon.de"))
    assert tranco_scorer.filter_it(rows) == []


def test_filter_preserves_rank():
    rows = _make_rows((42, "example.it"))
    result = tranco_scorer.filter_it(rows)
    assert result[0][0] == 42


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------

def test_score_prefers_higher_rank():
    """Lower rank number = higher score (rank 1 beats rank 1000)."""
    high = tranco_scorer.score(1, "foo.it")
    low = tranco_scorer.score(1000, "foo.it")
    assert high > low


def test_score_prefers_shorter_sld():
    """Same rank, shorter SLD wins."""
    short = tranco_scorer.score(100, "foo.it")
    long_ = tranco_scorer.score(100, "foobarlong.it")
    assert short > long_


def test_score_formula():
    """score = 1/rank + 1/len(sld)."""
    rank, domain = 10, "abc.it"
    sld_len = len("abc")
    expected = 1 / 10 + 1 / sld_len
    assert tranco_scorer.score(rank, domain) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# select
# ---------------------------------------------------------------------------

def test_select_returns_correct_sample_size():
    rows = [(i, f"domain{i}.it") for i in range(1, 101)]
    result = tranco_scorer.select(rows, pool=50, sample=10)
    assert len(result) == 10


def test_select_draws_from_top_pool_only():
    """With pool=5 from 100 rows, all sampled domains come from top-5 scored."""
    rows = [(i, f"x{i}.it") for i in range(1, 101)]  # rank 1..100
    # Top 5 by score are rank 1,2,3,4,5 (rank_score dominates for equal-length SLDs)
    top5_domains = {f"x{i}.it" for i in range(1, 6)}
    result = tranco_scorer.select(rows, pool=5, sample=5)
    result_domains = {d for _, d in result}
    assert result_domains <= top5_domains


def test_select_clamps_when_pool_exceeds_filtered_count(capsys):
    """If pool > available rows, use all rows and warn."""
    rows = [(1, "a.it"), (2, "b.it")]
    result = tranco_scorer.select(rows, pool=500, sample=2)
    assert len(result) == 2
    err = capsys.readouterr().err
    assert "warning" in err.lower()


def test_select_clamps_sample_when_pool_smaller(capsys):
    """If pool < sample, clamp sample to pool size and warn."""
    rows = [(i, f"d{i}.it") for i in range(1, 11)]
    result = tranco_scorer.select(rows, pool=3, sample=10)
    assert len(result) == 3
    err = capsys.readouterr().err
    assert "warning" in err.lower()


# ---------------------------------------------------------------------------
# write_csv
# ---------------------------------------------------------------------------

def test_write_csv_has_correct_columns(tmp_path):
    domains = [(1, "foo.it"), (2, "bar.it")]
    out = tmp_path / "domains.csv"
    tranco_scorer.write_csv(domains, out)
    rows = _read_csv(out)
    assert set(rows[0].keys()) == {"domain", "expiration_date", "notes"}


def test_write_csv_expiration_date_is_empty(tmp_path):
    domains = [(5, "test.it")]
    out = tmp_path / "domains.csv"
    tranco_scorer.write_csv(domains, out)
    rows = _read_csv(out)
    assert rows[0]["expiration_date"] == ""


def test_write_csv_notes_contains_tranco_rank(tmp_path):
    domains = [(42, "example.it")]
    out = tmp_path / "domains.csv"
    tranco_scorer.write_csv(domains, out)
    rows = _read_csv(out)
    assert rows[0]["notes"] == "tranco:42"


def test_write_csv_domain_column_is_correct(tmp_path):
    domains = [(1, "miosito.it")]
    out = tmp_path / "domains.csv"
    tranco_scorer.write_csv(domains, out)
    rows = _read_csv(out)
    assert rows[0]["domain"] == "miosito.it"

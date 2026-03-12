import pytest
from dnsexists import resolve


def test_resolve_returns_true_for_known_host():
    assert resolve("dns.google") is True


def test_resolve_returns_false_for_nonexistent_host():
    assert resolve("this-host-does-not-exist.invalid") is False

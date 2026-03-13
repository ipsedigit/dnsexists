import socket
from unittest.mock import MagicMock, patch
import pytest
from whois_client import query, is_registered, TLD_WHOIS_SERVERS


def _make_sock(chunks):
    sock = MagicMock()
    sock.recv.side_effect = list(chunks) + [b""]
    return sock


class TestQuery:
    def test_connects_to_port_43(self):
        sock = _make_sock([b"response"])
        with patch("socket.socket", return_value=sock):
            query("whois.example.com", "example.com")
        sock.connect.assert_called_once_with(("whois.example.com", 43))

    def test_sends_domain_with_crlf(self):
        sock = _make_sock([b"response"])
        with patch("socket.socket", return_value=sock):
            query("whois.example.com", "example.com")
        sock.sendall.assert_called_once_with(b"example.com\r\n")

    def test_returns_full_response_from_multiple_chunks(self):
        sock = _make_sock([b"first ", b"second"])
        with patch("socket.socket", return_value=sock):
            result = query("whois.example.com", "example.com")
        assert result == "first second"

    def test_applies_timeout(self):
        sock = _make_sock([b"response"])
        with patch("socket.socket", return_value=sock):
            query("whois.example.com", "example.com", timeout=3.0)
        sock.settimeout.assert_called_once_with(3.0)

    def test_decodes_invalid_utf8_with_replacement(self):
        sock = _make_sock([b"result \xff end"])
        with patch("socket.socket", return_value=sock):
            result = query("whois.example.com", "example.com")
        assert "\ufffd" in result


class TestIsRegistered:
    def _patch_query(self, response):
        return patch("whois_client.query", return_value=response)

    def test_no_match_for_pattern_returns_false(self):
        with self._patch_query("No match for EXAMPLE.COM."):
            assert is_registered("example.com") is False

    def test_not_found_pattern_returns_false(self):
        with self._patch_query("NOT FOUND"):
            assert is_registered("example.org") is False

    def test_no_entries_found_pattern_returns_false(self):
        with self._patch_query("No entries found for the selected source(s)."):
            assert is_registered("example.eu") is False

    def test_domain_not_found_pattern_returns_false(self):
        with self._patch_query("DOMAIN NOT FOUND"):
            assert is_registered("example.ai") is False

    def test_pattern_match_is_case_insensitive(self):
        with self._patch_query("no match for example.com"):
            assert is_registered("example.com") is False

    def test_registered_domain_returns_true(self):
        with self._patch_query("Domain: google.com\nRegistrar: MarkMonitor Inc."):
            assert is_registered("google.com") is True

    def test_empty_response_returns_true(self):
        with self._patch_query(""):
            assert is_registered("example.com") is True

    def test_socket_timeout_returns_true(self):
        with patch("whois_client.query", side_effect=socket.timeout):
            assert is_registered("example.com") is True

    def test_connection_refused_returns_true(self):
        with patch("whois_client.query", side_effect=ConnectionRefusedError):
            assert is_registered("example.com") is True

    def test_os_error_returns_true(self):
        with patch("whois_client.query", side_effect=OSError("network error")):
            assert is_registered("example.com") is True

    def test_unknown_tld_raises_value_error(self):
        with pytest.raises(ValueError):
            is_registered("example.invalidtld")

    def test_all_20_tlds_present_in_server_map(self):
        expected = {
            ".com", ".net", ".org", ".io", ".co", ".ai", ".dev", ".app",
            ".it", ".eu", ".info", ".biz", ".me", ".online", ".store",
            ".shop", ".tech", ".news", ".club", ".xyz",
        }
        assert set(TLD_WHOIS_SERVERS.keys()) == expected

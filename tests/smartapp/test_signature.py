# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock, call, patch

from requests import HTTPError

from smartapp.signature import retrieve_public_key


class TestSignatureVerifier:
    pass


@patch("smartapp.signature.requests.get")
class TestRetrievePublicKey:

    # This checks both the retry logic and the LRU cache.
    # Note that the LRU cache does not cache exceptions, only returned values.

    def test_retrieve_public_key_succeeds(self, get):
        response = MagicMock(text="public-key")
        response.raise_for_status = MagicMock()
        get.return_value = response
        key1 = retrieve_public_key("https://whatever.com", "key-succeeds")
        assert key1 == "public-key"
        key2 = retrieve_public_key("https://whatever.com", "key-succeeds")  # this call is cached
        assert key2 == "public-key"
        get.assert_called_once_with("https://whatever.com/key-succeeds")
        response.raise_for_status.assert_called_once()

    def test_retrieve_public_key_retry(self, get):
        response1 = MagicMock()
        response1.raise_for_status = MagicMock()
        response1.raise_for_status.side_effect = HTTPError("hello")
        response2 = MagicMock(text="public-key")
        response2.raise_for_status = MagicMock()
        get.side_effect = [response1, response2]
        key1 = retrieve_public_key("https://whatever.com", "key-retry")
        assert key1 == "public-key"
        key2 = retrieve_public_key("https://whatever.com", "key-retry")  # this call is cached
        assert key2 == "public-key"
        get.assert_has_calls([call("https://whatever.com/key-retry")] * 2)
        response1.raise_for_status.assert_called_once()
        response2.raise_for_status.assert_called_once()

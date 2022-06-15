# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name:
from unittest.mock import MagicMock, call, patch

import pendulum
import pytest
from requests import HTTPError

from smartapp.interface import SmartAppDefinition, SmartAppDispatcherConfig, SmartAppRequestContext
from smartapp.signature import SignatureVerifier, retrieve_public_key

# These tests are built on sample data on the Joyent documentation.
# See: https://github.com/TritonDataCenter/node-http-signature/blob/master/http_signing.md#appendix-a---test-values
#
# The sample request is:
#
#    POST /foo?param=value&pet=dog HTTP/1.1
#    Host: example.com
#    Date: Thu, 05 Jan 2014 21:31:40 GMT
#    Content-Type: application/json
#    Digest: SHA-256=X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE=
#    Content-Length: 18
#
#    {"hello": "world"}
#
# They also provide a public key and some sample signatures based on this request.
# In Joyent's documentation, there are two cases: the "default" case and the "all
# headers" case.  Below, the expected results are DEFAULTS_* and ALL_HEADERS_*.

METHOD = "POST"
HOST = "example.com"
PATH = "/foo?param=value&pet=dog"
REQUEST_TARGET = "post /foo?param=value&pet=dog"
DATE_STR = "Thu, 05 Jan 2014 21:31:40 GMT"
DATE_OBJ = pendulum.datetime(2014, 1, 5, 21, 31, 40, tz="GMT")
CONTENT_TYPE = "application/json"
CONTENT_LENGTH = "18"
DIGEST = "SHA-256=X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE="
BODY = '{"hello": "world"}'

KEY_ID = "Test"
ALGORITHM = "rsa-sha256"
CLOCK_SKEW = 300
KEYSERVER_URL = "https://key.smartthings.com"
KEY_DOWNLOAD_URL = "%s/%s" % (KEYSERVER_URL, KEY_ID)
SMARTAPP_URL = "https://%s%s" % (HOST, PATH)

DEFAULT_AUTHORIZATION = """
Signature keyId="Test",algorithm="rsa-sha256",signature="jKyvPcxB4JbmYY4mByyBY7cZfNl4OW9HpFQlG7N4YcJPteKTu4MWCLyk+gIr0wDgqtLWf9NLpMAMimdfsH7FSWGfbMFSrsVTHNTk0rK3usrfFnti1dxsM4jl0kYJCKTGI/UWkqiaxwNiKqGcdlEDrTcUhhsFsOIo8VhddmZTZ8w="
""".strip()

DEFAULT_SIGNATURE = """
jKyvPcxB4JbmYY4mByyBY7cZfNl4OW9HpFQlG7N4YcJPteKTu4MWCLyk+gIr0wDgqtLWf9NLpMAMimdfsH7FSWGfbMFSrsVTHNTk0rK3usrfFnti1dxsM4jl0kYJCKTGI/UWkqiaxwNiKqGcdlEDrTcUhhsFsOIo8VhddmZTZ8w=
""".strip()

DEFAULT_SIGNING_STRING = """
date: Thu, 05 Jan 2014 21:31:40 GMT
""".strip()

DEFAULT_ORIGINAL_HEADERS = {
    "Host": HOST,
    "Date": DATE_STR,
    "Content-Type": CONTENT_TYPE,
    "Digest": DIGEST,
    "Content-Length": CONTENT_LENGTH,
    "Authorization": DEFAULT_AUTHORIZATION,
}

DEFAULT_NORMALIZED_HEADERS = {
    "host": HOST,
    "date": DATE_STR,
    "content-type": CONTENT_TYPE,
    "digest": DIGEST,
    "content-length": CONTENT_LENGTH,
    "authorization": DEFAULT_AUTHORIZATION,
}

DEFAULT_SIGNING_HEADERS = "Date"

DEFAULT_SIGNING_ATTRIBUTES = {
    "keyId": KEY_ID,
    "headers": DEFAULT_SIGNING_HEADERS,
    "algorithm": ALGORITHM,
    "signature": DEFAULT_SIGNATURE,
}

ALL_HEADERS_AUTHORIZATION = """
Signature keyId="Test",algorithm="rsa-sha256",headers="(request-target) host date content-type digest content-length",signature="Ef7MlxLXoBovhil3AlyjtBwAL9g4TN3tibLj7uuNB3CROat/9KaeQ4hW2NiJ+pZ6HQEOx9vYZAyi+7cmIkmJszJCut5kQLAwuX+Ms/mUFvpKlSo9StS2bMXDBNjOh4Auj774GFj4gwjS+3NhFeoqyr/MuN6HsEnkvn6zdgfE2i0="
""".strip()

ALL_HEADERS_SIGNATURE = """
Ef7MlxLXoBovhil3AlyjtBwAL9g4TN3tibLj7uuNB3CROat/9KaeQ4hW2NiJ+pZ6HQEOx9vYZAyi+7cmIkmJszJCut5kQLAwuX+Ms/mUFvpKlSo9StS2bMXDBNjOh4Auj774GFj4gwjS+3NhFeoqyr/MuN6HsEnkvn6zdgfE2i0=
""".strip()

ALL_HEADERS_ORIGINAL_HEADERS = {
    "Host": HOST,
    "Date": DATE_STR,
    "Content-Type": CONTENT_TYPE,
    "Digest": DIGEST,
    "Content-Length": CONTENT_LENGTH,
    "Authorization": ALL_HEADERS_AUTHORIZATION,
}

ALL_HEADERS_NORMALIZED_HEADERS = {
    "host": HOST,
    "date": DATE_STR,
    "content-type": CONTENT_TYPE,
    "digest": DIGEST,
    "content-length": CONTENT_LENGTH,
    "authorization": ALL_HEADERS_AUTHORIZATION,
}

ALL_HEADERS_SIGNING_HEADERS = "(request-target) host date content-type digest content-length"

ALL_HEADERS_SIGNING_ATTRIBUTES = {
    "keyId": KEY_ID,
    "headers": ALL_HEADERS_SIGNING_HEADERS,
    "algorithm": ALGORITHM,
    "signature": ALL_HEADERS_SIGNATURE,
}

ALL_HEADERS_SIGNING_STRING = """
(request-target): post /foo?param=value&pet=dog
host: example.com
date: Thu, 05 Jan 2014 21:31:40 GMT
content-type: application/json
digest: SHA-256=X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE=
content-length: 18
""".strip()


PUBLIC_SIGNING_KEY = """
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDCFENGw33yGihy92pDjZQhl0C3
6rPJj+CvfSC8+q28hxA161QFNUd13wuCTUcq0Qd2qsBe/2hFyc2DCJJg0h1L78+6
Z4UMR7EOcpfdUE9Hf3m/hs+FUR45uBJeDK1HSFHD8bHKD6kv8FPGfJTotc+2xjJw
oYi+1hqp1fIekaxsyQIDAQAB
-----END PUBLIC KEY-----
""".strip()


@pytest.fixture
def config() -> SmartAppDispatcherConfig:
    return SmartAppDispatcherConfig(
        check_signatures=True,
        clock_skew_sec=CLOCK_SKEW,
        key_server_url=KEYSERVER_URL,
    )


@pytest.fixture
def definition() -> SmartAppDefinition:
    return SmartAppDefinition(
        id="",
        name="",
        description="",
        target_url=SMARTAPP_URL,
        permissions=[],
        config_pages=[],
    )


@pytest.fixture
def default_context() -> SmartAppRequestContext:
    return SmartAppRequestContext(body=BODY, headers=DEFAULT_ORIGINAL_HEADERS)


@pytest.fixture
def all_headers_context() -> SmartAppRequestContext:
    return SmartAppRequestContext(body=BODY, headers=ALL_HEADERS_ORIGINAL_HEADERS)


class TestSignatureVerifier:
    def test_default_signature_attributes(self, default_context, config, definition):
        verifier = SignatureVerifier(context=default_context, config=config, definition=definition)
        assert verifier.headers == DEFAULT_NORMALIZED_HEADERS
        assert verifier.body == BODY
        assert verifier.method == METHOD
        assert verifier.path == PATH
        assert verifier.request_target == REQUEST_TARGET
        assert verifier.date == DATE_OBJ
        assert verifier.authorization == DEFAULT_AUTHORIZATION
        assert verifier.signing_attributes == DEFAULT_SIGNING_ATTRIBUTES
        assert verifier.key_id == KEY_ID
        assert verifier.keyserver_url == KEYSERVER_URL
        assert verifier.algorithm == ALGORITHM
        assert verifier.signature == DEFAULT_SIGNATURE
        assert verifier.digest == DIGEST
        assert verifier.signing_string == DEFAULT_SIGNING_STRING

    def test_all_headers_signature_attributes(self, all_headers_context, config, definition):
        verifier = SignatureVerifier(context=all_headers_context, config=config, definition=definition)
        assert verifier.headers == ALL_HEADERS_NORMALIZED_HEADERS
        assert verifier.body == BODY
        assert verifier.method == METHOD
        assert verifier.path == PATH
        assert verifier.request_target == REQUEST_TARGET
        assert verifier.date == DATE_OBJ
        assert verifier.authorization == ALL_HEADERS_AUTHORIZATION
        assert verifier.signing_attributes == ALL_HEADERS_SIGNING_ATTRIBUTES
        assert verifier.key_id == KEY_ID
        assert verifier.keyserver_url == KEYSERVER_URL
        assert verifier.algorithm == ALGORITHM
        assert verifier.signature == ALL_HEADERS_SIGNATURE
        assert verifier.digest == DIGEST
        assert verifier.signing_string == ALL_HEADERS_SIGNING_STRING


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

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name:
from typing import Dict, Optional
from unittest.mock import MagicMock, call, patch

import pendulum
import pytest
from requests import HTTPError

from smartapp.interface import SignatureError, SmartAppDefinition, SmartAppDispatcherConfig, SmartAppRequestContext
from smartapp.signature import SignatureVerifier, retrieve_public_key

# These tests are built on sample data found in the Joyent specification.
# See: https://github.com/TritonDataCenter/node-http-signature/blob/master/http_signing.md#appendix-a---test-values
#
# Joyent provides a sample request and also a public key and some sample signatures based
# on this request.  The sample request is::
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
# The public key is stored below in `PUBLIC_SIGNING_KEY`
#
# In Joyent's documentation, there are two cases: the "default" case and the "all
# headers" case.  Below, the expected results are DEFAULTS_* and ALL_HEADERS_*.


METHOD = "POST"
HOST = "example.com"
PATH = "/foo?param=value&pet=dog"
REQUEST_TARGET = "post /foo?param=value&pet=dog"
DATE_STR = "Thu, 05 Jan 2014 21:31:40 GMT"
DATE_OBJ = pendulum.datetime(2014, 1, 5, 21, 31, 40, tz="GMT")
BODY = '{"hello": "world"}'
CONTENT_TYPE = "application/json"
CONTENT_LENGTH = str(len(BODY))  # should be 18
DIGEST = "SHA-256=X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE="

CORRELATION = "XXX"
KEY_ID = "Test"
ALGORITHM = "rsa-sha256"
CLOCK_SKEW = 300
KEYSERVER_URL = "https://key.smartthings.com"
KEY_DOWNLOAD_URL = "%s/%s" % (KEYSERVER_URL, KEY_ID)
SMARTAPP_URL = "https://%s%s" % (HOST, PATH)

# public key used for the sample Joyent signatures
PUBLIC_SIGNING_KEY = """
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDCFENGw33yGihy92pDjZQhl0C3
6rPJj+CvfSC8+q28hxA161QFNUd13wuCTUcq0Qd2qsBe/2hFyc2DCJJg0h1L78+6
Z4UMR7EOcpfdUE9Hf3m/hs+FUR45uBJeDK1HSFHD8bHKD6kv8FPGfJTotc+2xjJw
oYi+1hqp1fIekaxsyQIDAQAB
-----END PUBLIC KEY-----
""".strip()

# a valid public key, just not the one used in Joyent's sample data
WRONG_SIGNING_KEY = """
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDTt945+S+6dhkvVQXH4E4Dy6hc
KqQ5Z4FSvwfXnu23sZ15A9vx43imVJE5bS0H6n893nh9RNvrYp98nGcQLLVhvdTq
wIpl+cWCurqGtwkAAqmNjXwCbj69hUHGXtqX3Jn5MKB5IghjEDU4N3dFGoCWWycb
4l8BNIcle/5s7Vo9vwIDAQAB
-----END PUBLIC KEY-----
""".strip()

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
    "x-st-correlation": CORRELATION,
}

DEFAULT_NORMALIZED_HEADERS = {
    "host": HOST,
    "date": DATE_STR,
    "content-type": CONTENT_TYPE,
    "digest": DIGEST,
    "content-length": CONTENT_LENGTH,
    "authorization": DEFAULT_AUTHORIZATION,
    "x-st-correlation": CORRELATION,
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


def build_config(clock_skew_sec: Optional[int] = CLOCK_SKEW) -> SmartAppDispatcherConfig:
    """Build configuration to test with."""
    return SmartAppDispatcherConfig(
        check_signatures=True,
        clock_skew_sec=clock_skew_sec,
        key_server_url=KEYSERVER_URL,
    )


def build_definition(target_url: str = SMARTAPP_URL) -> SmartAppDefinition:
    """Build a SmartApp definition to test with."""
    return SmartAppDefinition(
        id="",
        name="",
        description="",
        target_url=target_url,
        permissions=[],
        config_pages=[],
    )


def build_context(headers: Dict[str, str]) -> SmartAppRequestContext:
    """Build a request context to test with."""
    return SmartAppRequestContext(body=BODY, headers=headers)


class TestSignatureVerifier:

    # TODO: I need better coverage here; I think the way I'm structuring the fixtures
    #       is not as flexible as I need, because I want to have various different kinds
    #       of bad configuration, or missing values, etc., etc.

    def test_default_signature_attributes(self):
        # technically, if we can properly verify a valid or invalid a signature, these are irrelevant
        # however, checking them helps us confirm that we have the right inputs to the algorithm
        context = build_context(headers=DEFAULT_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        assert verifier.correlation_id == CORRELATION
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

    def test_all_headers_signature_attributes(self):
        # technically, if we can properly verify a valid or invalid a signature, these are irrelevant
        # however, checking them helps us confirm that we have the right inputs to the algorithm
        context = build_context(headers=ALL_HEADERS_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        assert verifier.correlation_id is None  # because the header isn't in ALL_HEADERS_ORIGINAL_HEADERS
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

    @patch("smartapp.signature.now")
    @pytest.mark.parametrize(
        "date",
        [
            DATE_OBJ.subtract(seconds=CLOCK_SKEW),
            DATE_OBJ.subtract(seconds=CLOCK_SKEW).add(seconds=1),
            DATE_OBJ.subtract(seconds=CLOCK_SKEW).add(seconds=2),
            DATE_OBJ,
            DATE_OBJ.add(seconds=CLOCK_SKEW).subtract(seconds=2),
            DATE_OBJ.add(seconds=CLOCK_SKEW).subtract(seconds=1),
            DATE_OBJ.add(seconds=CLOCK_SKEW),
        ],
    )
    def test_verify_date_valid(self, now, date):
        # with a clock skew set, anything inclusively within the configured skew is valid
        context = build_context(headers=DEFAULT_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        now.return_value = date
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        verifier.verify_date()

    @patch("smartapp.signature.now")
    @pytest.mark.parametrize(
        "date",
        [
            DATE_OBJ.subtract(seconds=CLOCK_SKEW).subtract(seconds=2),
            DATE_OBJ.subtract(seconds=CLOCK_SKEW).subtract(seconds=1),
            DATE_OBJ.add(seconds=CLOCK_SKEW).add(seconds=1),
            DATE_OBJ.add(seconds=CLOCK_SKEW).add(seconds=2),
        ],
    )
    def test_verify_date_invalid(self, now, date):
        # with a clock skew set, anything 1 second or more outside the configured skew is invalid
        context = build_context(headers=DEFAULT_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        now.return_value = date
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        with pytest.raises(SignatureError, match="Request date is not current") as e:
            verifier.verify_date()
        assert e.value.correlation_id == context.correlation_id

    @patch("smartapp.signature.now")
    @pytest.mark.parametrize(
        "date",
        [
            DATE_OBJ.subtract(seconds=CLOCK_SKEW).subtract(seconds=2),
            DATE_OBJ.subtract(seconds=CLOCK_SKEW).subtract(seconds=1),
            DATE_OBJ.subtract(seconds=CLOCK_SKEW),
            DATE_OBJ.subtract(seconds=CLOCK_SKEW).add(seconds=1),
            DATE_OBJ.subtract(seconds=CLOCK_SKEW).add(seconds=2),
            DATE_OBJ,
            DATE_OBJ.add(seconds=CLOCK_SKEW).subtract(seconds=2),
            DATE_OBJ.add(seconds=CLOCK_SKEW).subtract(seconds=1),
            DATE_OBJ.add(seconds=CLOCK_SKEW),
            DATE_OBJ.add(seconds=CLOCK_SKEW).add(seconds=1),
            DATE_OBJ.add(seconds=CLOCK_SKEW).add(seconds=2),
        ],
    )
    def test_verify_date_no_skew(self, now, date):
        # with clock skew set to None (via no_skew_config) any date is valid
        context = build_context(headers=DEFAULT_ORIGINAL_HEADERS)
        config = build_config(clock_skew_sec=None)
        definition = build_definition()
        now.return_value = date
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        verifier.verify_date()

    @patch("smartapp.signature.retrieve_public_key")
    @patch("smartapp.signature.now")
    def test_default_verify_valid(self, now, retrieve):
        # with a valid key from the Joyent sample data, everything should line up and we should have a valid signature
        context = build_context(headers=DEFAULT_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        now.return_value = DATE_OBJ
        retrieve.return_value = PUBLIC_SIGNING_KEY
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        verifier.verify()
        retrieve.assert_called_once_with(KEYSERVER_URL, KEY_ID)

    @patch("smartapp.signature.retrieve_public_key")
    @patch("smartapp.signature.now")
    def test_all_headers_verify_valid(self, now, retrieve):
        # with a valid key from the Joyent sample data, everything should line up and we should have a valid signature
        context = build_context(headers=DEFAULT_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        now.return_value = DATE_OBJ
        retrieve.return_value = PUBLIC_SIGNING_KEY
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        verifier.verify()
        retrieve.assert_called_once_with(KEYSERVER_URL, KEY_ID)

    @patch("smartapp.signature.retrieve_public_key")
    @patch("smartapp.signature.now")
    def test_default_verify_invalid_key(self, now, retrieve):
        # with an invalid key, the signature can never be valid
        context = build_context(headers=DEFAULT_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        now.return_value = DATE_OBJ
        retrieve.return_value = "bogus"
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        with pytest.raises(SignatureError, match="Signature is not valid") as e:
            verifier.verify()
        assert e.value.correlation_id == context.correlation_id

    @patch("smartapp.signature.retrieve_public_key")
    @patch("smartapp.signature.now")
    def test_all_headers_verify_invalid_key(self, now, retrieve):
        # with an invalid key, the signature can never be valid
        context = build_context(headers=ALL_HEADERS_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        now.return_value = DATE_OBJ
        retrieve.return_value = "bogus"
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        with pytest.raises(SignatureError, match="Signature is not valid") as e:
            verifier.verify()
        assert e.value.correlation_id == context.correlation_id

    @patch("smartapp.signature.retrieve_public_key")
    @patch("smartapp.signature.now")
    def test_default_verify_wrong_key(self, now, retrieve):
        # with the wrong key, the signature can never be valid
        context = build_context(headers=DEFAULT_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        now.return_value = DATE_OBJ
        retrieve.return_value = WRONG_SIGNING_KEY
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        with pytest.raises(SignatureError, match="Signature is not valid") as e:
            verifier.verify()
        assert e.value.correlation_id == context.correlation_id

    @patch("smartapp.signature.retrieve_public_key")
    @patch("smartapp.signature.now")
    def test_all_headers_verify_wrong_key(self, now, retrieve):
        # with the wrong key, the signature can never be valid
        context = build_context(headers=ALL_HEADERS_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition()
        now.return_value = DATE_OBJ
        retrieve.return_value = WRONG_SIGNING_KEY
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        with pytest.raises(SignatureError, match="Signature is not valid") as e:
            verifier.verify()
        assert e.value.correlation_id == context.correlation_id

    @patch("smartapp.signature.retrieve_public_key")
    @patch("smartapp.signature.now")
    def test_default_verify_mismatch(self, now, retrieve):
        # this has a Date header that does not match the Joyent sample, causing an invalid signature
        headers = DEFAULT_ORIGINAL_HEADERS.copy()
        headers["Date"] = "Tue, 14 Jun 2022 21:23:01 GMT"  # different date than in Joyent sample
        context = build_context(headers)
        config = build_config()
        definition = build_definition()
        now.return_value = DATE_OBJ
        retrieve.return_value = PUBLIC_SIGNING_KEY
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        assert verifier.signing_string != DEFAULT_SIGNING_STRING
        with pytest.raises(SignatureError, match="Request date is not current") as e:
            verifier.verify()
        assert e.value.correlation_id == context.correlation_id

    @patch("smartapp.signature.retrieve_public_key")
    @patch("smartapp.signature.now")
    def test_all_headers_verify_mismatch(self, now, retrieve):
        # the bad_definition contains a URL that doesn't match the Joyent sample
        # we will generate a bad signing string and hence the signature is invalid
        context = build_context(headers=ALL_HEADERS_ORIGINAL_HEADERS)
        config = build_config()
        definition = build_definition(target_url="https://whatever.com/smartapp")  # does not match Joyent's example
        now.return_value = DATE_OBJ
        retrieve.return_value = PUBLIC_SIGNING_KEY
        verifier = SignatureVerifier(context=context, config=config, definition=definition)
        assert verifier.signing_string != ALL_HEADERS_SIGNING_STRING
        with pytest.raises(SignatureError, match="Signature is not valid") as e:
            verifier.verify()
        assert e.value.correlation_id == context.correlation_id


@patch("smartapp.signature.requests.get")
class TestRetrievePublicKey:

    # This checks both the retry logic and the LRU cache.
    # Note that the LRU cache does not cache exceptions, only returned values.

    def test_retrieve_public_key_succeeds(self, get):
        response = MagicMock(text="public-key")
        response.raise_for_status = MagicMock()
        get.return_value = response
        key1 = retrieve_public_key("https://whatever.com", "key-succeeds")  # note: no leading slash
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
        key1 = retrieve_public_key("https://whatever.com", "/key-retry")  # note: leading slash
        assert key1 == "public-key"
        key2 = retrieve_public_key("https://whatever.com", "/key-retry")  # this call is cached
        assert key2 == "public-key"
        get.assert_has_calls([call("https://whatever.com/key-retry")] * 2)
        response1.raise_for_status.assert_called_once()
        response2.raise_for_status.assert_called_once()

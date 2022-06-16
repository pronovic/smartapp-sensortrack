# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Verify HTTP signatures on SmartApp lifecycle event requests.
"""

# This implements HTTP signature verification for the SmartApp lifecycle events.
# See: https://developer-preview.smartthings.com/docs/connected-services/hosting/webhook-smartapp/
#
# SmartThings uses Joyent's HTTP signature scheme to signal all lifecycle events.
# See: https://github.com/TritonDataCenter/node-http-signature/blob/master/http_signing.md
#
# Note that only the rsa-sha256 algorithm is supported in this code.  As far as I can
# tell, this is the only one SmartThings uses.  Limiting to the single algorithm greatly
# simplifies the implementation, plus we can use the test cases that Joylent includes in
# their specification document in our own unit tests.
#
# The crypto implementation is PyCryptodome. There are other options, but this appears to
# be well-maintained, is fairly popular (2000+ GitHub stars), and the documentation is good.
# See: https://pypi.org/project/pycryptodomex/ and https://www.pycryptodome.org/en/latest/
#
# The derived signature attributes are in some sense private to the implementation, and in
# some sense public, since they are inputs to the Joyent signature algorithm itself.  I've
# chosen to make them public and read-only on `SignatureVerifier`, which makes the
# implementation more transparent and also makes it easier to verify the implementation
# using the sample data provided in the Joyent spec.
#
# The retrieve_public_key() function is implemented as a function so we can cache the
# result and implement retries outside of SignatureVerifier.  We retry up to 5 times (6
# total attempts), waiting 0.25 seconds before first retry, and limiting the wait between
# retries to 2 seconds.  This is not configurable.  Note that the LRU cache only caches
# responses, not any exceptions that were thrown.

import logging
import re
import urllib.parse
from base64 import b64decode
from functools import lru_cache
from typing import List, Mapping, Optional

import requests
from attrs import field, frozen
from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import pkcs1_15
from pendulum import from_format, now
from pendulum.datetime import DateTime
from requests import ConnectionError as RequestsConnectionError
from requests import HTTPError, RequestException
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from .interface import SignatureError, SmartAppDefinition, SmartAppDispatcherConfig, SmartAppRequestContext


@lru_cache(maxsize=32)
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.25, max=2),
    retry=retry_if_exception_type((RequestsConnectionError, HTTPError)),
)
def retrieve_public_key(key_server_url: str, key_id: str) -> str:
    """Retrieve a public key, caching the result."""
    # Note that the key ID is assumed to be URL-safe per notes in the SmartThings spec, so we don't encode it
    url = "%s/%s" % (key_server_url, key_id.lstrip("/"))
    response = requests.get(url)
    response.raise_for_status()
    return response.text


DATE_FORMAT = "DD MMM YYYY HH:mm:ss z"  # like "05 Jan 2014 21:31:40 GMT"; we strip off the leading day of week

# noinspection PyUnresolvedReferences
@frozen(kw_only=True, repr=True)
class SignatureVerifier:

    """Signature verifier for Joyent HTTP signatures."""

    context: SmartAppRequestContext = field(repr=False)  # because context.body may contain secrets
    config: SmartAppDispatcherConfig = field()
    definition: SmartAppDefinition = field()
    correlation_id: Optional[str] = field(init=False)
    body: str = field(init=False)
    content_length: int = field(init=False)
    method: str = field(init=False)
    path: str = field(init=False)
    request_target: str = field(init=False)
    date: DateTime = field(init=False)
    authorization: str = field(init=False)
    signing_attributes: Mapping[str, str] = field(init=False)
    signing_headers: str = field(init=False)
    key_id: str = field(init=False)
    keyserver_url: str = field(init=False)
    algorithm: str = field(init=False)
    signature: str = field(init=False)
    signing_string: str = field(init=False)

    @correlation_id.default
    def _default_correlation_id(self) -> Optional[str]:
        return self.context.correlation_id

    @body.default
    def _default_body(self) -> str:
        return self.context.body

    @method.default
    def _default_method(self) -> str:
        return "POST"  # this is the only method ever used by the SmartApp interface

    @path.default
    def _default_path(self) -> str:
        # The path from the configured endpoint might be different than what the server served, due to forwarding
        parts = urllib.parse.urlsplit(self.definition.target_url)
        path = parts.path
        if parts.query:
            path = "%s?%s" % (path, parts.query)
        return path

    @request_target.default
    def _default_request_target(self) -> str:
        return "%s %s" % (self.method.lower(), self.path)

    @authorization.default
    def _default_authorization(self) -> str:
        return self.header("authorization")

    @date.default
    def _default_date(self) -> DateTime:
        return from_format(self.header("date")[5:], DATE_FORMAT)  # remove the day ("Thu, ") from front

    @signing_attributes.default
    def _default_signing_attributes(self) -> Mapping[str, str]:
        # We're parsing a string like: 'Signature keyId="key",algorithm="rsa-sha256",headers="date",signature="xxx"'
        def attribute(name: str, default: Optional[str] = None) -> str:
            if not self.authorization.startswith("Signature "):
                raise SignatureError("Authorization header is not a signature", self.correlation_id)
            pattern = r"(%s=\")([^\"]+?)(\")" % name
            match = re.search(pattern=pattern, string=self.authorization)
            if not match:
                if default:
                    return default
                raise SignatureError("Signature does not contain: %s" % name, self.correlation_id)
            return match.group(2)

        return {
            "keyId": attribute("keyId"),
            "headers": attribute("headers", default="Date"),
            "algorithm": attribute("algorithm"),
            "signature": attribute("signature"),
        }

    @signing_headers.default
    def _default_signing_headers(self) -> List[str]:
        # We're parsing a string like "(request-target) date content-type digest" into a list
        return self.signing_attributes["headers"].strip().split(" ")

    @key_id.default
    def _default_key_id(self) -> str:
        return self.signing_attributes["keyId"]

    @keyserver_url.default
    def _default_keyserver_url(self) -> str:
        return self.config.keyserver_url

    @algorithm.default
    def _default_algorithm(self) -> str:
        algorithm = self.signing_attributes["algorithm"]
        if algorithm != "rsa-sha256":
            raise SignatureError("Algorithm not supported: %s" % algorithm, self.correlation_id)
        return algorithm

    @signature.default
    def _default_signature(self) -> str:
        return self.signing_attributes["signature"]

    @signing_string.default
    def _signing_string(self) -> str:
        # The only "special" component in the signing string is "(request-target)"
        # Everything else must be found as a header, and we should fail if it's not
        components = []
        for name in self.signing_headers:
            if name == "(request-target)":
                components.append("(request-target): %s" % self.request_target)
            else:
                components.append("%s: %s" % (name.lower(), self.header(name)))
        return "\n".join(components).rstrip("\n")

    def header(self, name: str) -> str:
        """Return the named header case-insensitively, raising SignatureError if it is not found or is empty"""
        value = self.context.header(name)
        if not value:
            raise SignatureError("Header not found: %s" % name, self.correlation_id)
        return value

    def retrieve_public_key(self) -> str:
        """Retrieve the configured public key."""
        try:
            return retrieve_public_key(self.keyserver_url, self.key_id)  # will retry automatically
        except RequestException as e:
            raise SignatureError("Failed to retrieve key [%s]" % self.key_id, self.correlation_id) from e

    def verify_date(self) -> None:
        """Verify the date, ensuring that it is current per skew configuration."""
        if self.config.clock_skew_sec is not None:
            skew = abs(now() - self.date)
            if skew.seconds > self.config.clock_skew_sec:
                raise SignatureError("Request date is not current, skew of %d seconds" % skew.seconds, self.correlation_id)

    def verify_signature(self) -> None:
        """Verify the RSA-SHA256 signature of the signing string."""
        # See: https://www.pycryptodome.org/en/latest/src/signature/pkcs1_v1_5.html
        try:
            logging.debug("[%s] Signing string: \n%s", self.correlation_id, self.signing_string)
            signature = b64decode(self.signature)
            sha256 = SHA256.new(self.signing_string.encode())
            key = RSA.import_key(self.retrieve_public_key())
            pkcs1_15.new(key).verify(sha256, signature)
        except (ValueError, TypeError) as e:
            raise SignatureError("Signature is not valid", self.correlation_id) from e

    def verify(self) -> None:
        """Verify the request date and the signature of the signing string."""
        self.verify_date()
        self.verify_signature()

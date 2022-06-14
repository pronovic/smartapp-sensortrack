# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Verify HTTP signatures on SmartApp lifecycle event requests.
"""

# This implements HTTP signature verification for the SmartApp lifecycle events.
# See: https://developer-preview.smartthings.com/docs/connected-services/hosting/webhook-smartapp/
#
# SmartThings uses Joyent's HTTP signature scheme.  Note that only the rsa-sha256 algorithm
# is supported in this code.  As far as I can tell, this is the only one SmartThings uses.
# Limiting to the single algorithm greatly simplifies the implementation, plus we can use
# the test cases that Joylent includes in their specification document in our own unit tests.
# See: https://github.com/TritonDataCenter/node-http-signature/blob/master/http_signing.md
#
# The crypto implementation is PyCryptodome. There are other options, but this appears to
# be well-maintained, is fairly popular (2000+ GitHub stars), and the documentation is good.
# See: https://pypi.org/project/pycryptodomex/ and https://www.pycryptodome.org/en/latest/

import re
import urllib.parse
from base64 import b64encode
from functools import lru_cache
from typing import List, Mapping

import requests
from attrs import field, frozen
from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import pkcs1_15
from pendulum import now
from pendulum.datetime import DateTime
from pendulum.parser import parse
from requests import ConnectionError as RequestsConnectionError
from requests import HTTPError, RequestException
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from .interface import SignatureError, SmartAppDefinition, SmartAppDispatcherConfig, SmartAppRequestContext

# This is implemented as a function so we can cache the result and implement retries
# outside of SignatureVerifier.  We retry up to 5 times (6 total attempts), waiting
# 0.25 seconds before first retry, and limiting the wait between retries to 2 seconds.
# Note that the LRU cache only caches responses, not any exceptions that were thrown.


@lru_cache(maxsize=32)
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.25, max=2),
    retry=retry_if_exception_type((RequestsConnectionError, HTTPError)),
)
def retrieve_public_key(key_server_url: str, key_id: str) -> str:
    """Retrieve a public key, caching the result."""
    # Note that the key ID is assumed to be URL-safe, and so we don't encode it
    url = "%s/%s" % (key_server_url, key_id)
    response = requests.get(url)
    response.raise_for_status()
    return response.text


# noinspection PyUnresolvedReferences
@frozen(kw_only=True, repr=False)
class SignatureVerifier:

    context: SmartAppRequestContext
    config: SmartAppDispatcherConfig
    definition: SmartAppDefinition
    body: str = field(init=False)
    method: str = field(init=False)
    path: str = field(init=False)
    request_target: str = field(init=False)
    date: DateTime = field(init=False)
    authorization: str = field(init=False)
    signing_attributes: Mapping[str, str] = field(init=False)
    key_id: str = field(init=False)
    key_url: str = field(init=False)
    algorithm: str = field(init=False)
    digest: str = field(init=False)
    signing_headers: str = field(init=False)
    signing_string: str = field(init=False)
    signature: str = field(init=False)

    @body.default
    def _default_body(self) -> str:
        return self.context.body

    @method.default
    def _default_method(self) -> str:
        return "POST"  # this is the only method ever used by the SmartApp interface

    @path.default
    def _default_path(self) -> str:
        # The path from the configured endpoint might be different than what the server served, due to forwarding
        return urllib.parse.urlparse(self.definition.target_url).path

    @request_target.default
    def _default_request_target(self) -> str:
        return "%s %s" % (self.method.lower(), self.path)

    @authorization.default
    def _default_authorization(self) -> str:
        return self.header("authorization")

    @date.default
    def _default_date(self) -> DateTime:
        return parse(self.header("date"))  # type: ignore

    @signing_attributes.default
    def _default_signing_attributes(self) -> Mapping[str, str]:
        # We're parsing a string like: 'Signature keyId="key",algorithm="rsa-sha256",headers="date",signature="xxx"'
        def attribute(name: str) -> str:
            if not self.authorization.startswith("Signature "):
                raise SignatureError("Authorization header is not a signature")
            pattern = r"(%s=\")([^\"]+?)(\")" % name
            match = re.search(pattern=pattern, string=self.authorization)
            if not match:
                raise SignatureError("Signature does not contain: %s" % name)
            return match.group(2)

        return {name: attribute(name) for name in ["keyId", "headers", "algorithm", "signature"]}

    @key_id.default
    def _default_key_id(self) -> str:
        return self.signing_attributes["keyId"]

    @key_url.default
    def _default_key_server_url(self) -> str:
        return self.config.key_server_url

    @algorithm.default
    def _default_algorithm(self) -> str:
        algorithm = self.signing_attributes["algorithm"]
        if algorithm != "rsa-sha256":
            raise SignatureError("Algorithm not supported: %s" % algorithm)
        return algorithm

    @signature.default
    def _default_signature(self) -> str:
        return self.signing_attributes["signature"]

    @digest.default
    def _default_digest(self) -> str:
        data = self.body.encode()
        digest = SHA256.new(data=data).digest()
        base64 = b64encode(digest).decode("ascii")
        return "SHA-256=%s" % base64

    @signing_headers.default
    def _default_signing_headers(self) -> List[str]:
        # We're parsing a string like "(request-target) date content-type digest" into a list
        return self.signing_attributes["headers"].strip().split(" ")

    @signing_string.default
    def _signing_string(self) -> str:
        components = []
        for name in self.signing_headers:
            if name == "(request-target)":
                components.append("(request-target): %s" % self.request_target)
            elif name == "digest":
                components.append("digest: %s" % self.digest)
            else:
                components.append("%s: %s" % (name, self.header(name)))
        return "\n".join(components).rstrip("\n")

    def header(self, name: str) -> str:
        """Return the named header, raising SignatureError if it is not found or is empty"""
        if not name in self.context.headers:
            raise SignatureError("Header not found: %s" % name)
        value = self.context.headers[name]
        if not value or not value.strip():
            raise SignatureError("Header not found: %s" % name)
        return value

    def retrieve_public_key(self) -> str:
        """Retrieve the configured public key."""
        try:
            return retrieve_public_key(self.key_url, self.key_id)  # will retry automatically
        except RequestException as e:
            raise SignatureError("Failed to retrieve key [%s]" % self.key_id) from e

    def verify_date(self) -> None:
        """Verify the date, ensuring that it is current per skew configuration."""
        if self.config.clock_skew_sec is not None:
            skew = now() - self.date
            if abs(skew.seconds) > self.config.clock_skew_sec:
                raise SignatureError("Request date is not current, skew of %d seconds" % skew.seconds)

    def verify_signature(self) -> None:
        """Verify the RSA-SHA256 signature of the signing string."""
        # See: https://www.pycryptodome.org/en/latest/src/signature/pkcs1_v1_5.html
        try:
            key = RSA.import_key(self.retrieve_public_key())
            sha256 = SHA256.new(self.signing_string.encode())
            pkcs1_15.new(key).verify(sha256, self.signature.encode())
        except (ValueError, TypeError) as e:
            raise SignatureError("Signature is not valid") from e

    def verify(self) -> None:
        """Verify the request date and the signature of the signing string."""
        self.verify_date()
        self.verify_signature()

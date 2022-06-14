# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Verify HTTP signatures on SmartApp lifecycle event requests.
"""

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

from smartapp.interface import SignatureError, SmartAppDefinition, SmartAppDispatcherConfig, SmartAppRequestContext

REQUEST_TARGET = "(request-target)"
DIGEST = "digest"
AUTHORIZATION = "authorization"


@lru_cache(maxsize=32)
def _retrieve_public_key(key_server_url: str, key_id: str) -> str:
    """Retrieve a public key, caching the result."""
    url = "%s/%s" % (key_server_url, key_id)
    response = requests.get(url)
    if not response.ok:
        raise SignatureError("Failed to retrieve key: %s" % key_id)
    return response.text


def verify_rsa_sha256_signature(public_key: str, message: str, signature: str) -> None:
    """Verify an RSA-SHA256 signature for a message."""
    try:
        key = RSA.import_key(public_key)
        sha256 = SHA256.new(message.encode())
        pkcs1_15.new(key).verify(sha256, signature.encode())
    except (ValueError, TypeError) as e:
        raise SignatureError("Signature is not valid") from e


@frozen(kw_only=True, repr=False)
class SignatureContext:

    context: SmartAppRequestContext
    config: SmartAppDispatcherConfig
    definition: SmartAppDefinition
    body: str = field()
    method: str = field()
    path: str = field()
    request_target: str = field()
    authorization: str = field()
    signing_attributes: Mapping[str, str] = field()
    key_id: str = field()
    key_url: str = field()
    algorithm: str = field()
    digest: str = field()
    signing_headers: str = field()
    signing_string: str = field()
    signature: str = field()

    # noinspection PyUnresolvedReferences
    @body.default
    def _default_body(self) -> str:
        return self.context.body

    # noinspection PyUnresolvedReferences
    @method.default
    def _default_method(self) -> str:
        return "POST"  # this is the only method ever used by the SmartApp interface

    # noinspection PyUnresolvedReferences
    @path.default
    def _default_path(self) -> str:
        # We need to use the path from the configured endpoint, which might
        # be different than the server served, due to forwarding.
        return urllib.parse.urlparse(self.definition.target_url).path

    # noinspection PyUnresolvedReferences
    @request_target.default
    def _default_request_target(self) -> str:
        return "%s %s" % (self.method.lower(), self.path)

    # noinspection PyUnresolvedReferences
    @authorization.default
    def _default_authorization(self) -> str:
        return self.header(AUTHORIZATION)

    # noinspection PyUnresolvedReferences
    @signing_attributes.default
    def _default_signing_attributes(self) -> Mapping[str, str]:
        def attribute(name: str) -> str:
            if not self.authorization.startswith("Signature "):
                raise SignatureError("Authorization header is not a signature")
            pattern = r"(%s=\")([^\"]+?)(\")" % name
            match = re.search(pattern=pattern, string=self.authorization)
            if not match:
                raise SignatureError("Signature does not contain: %s" % name)
            return match.group(2)

        return {name: attribute(name) for name in ["keyId", "headers", "algorithm", "signature"]}

    # noinspection PyUnresolvedReferences
    @key_id.default
    def _default_key_id(self) -> str:
        return self.signing_attributes["keyId"]

    # noinspection PyUnresolvedReferences
    @key_url.default
    def _default_key_server_url(self) -> str:
        return self.config.key_server_url

    # noinspection PyUnresolvedReferences
    @algorithm.default
    def _default_algorithm(self) -> str:
        algorithm = self.signing_attributes["algorithm"]
        if algorithm != "rsa-sha256":
            raise SignatureError("Algorithm not supported: %s" % algorithm)
        return algorithm

    # noinspection PyUnresolvedReferences
    @signature.default
    def _default_signature(self) -> str:
        return self.signing_attributes["signature"]

    # noinspection PyUnresolvedReferences
    @digest.default
    def _default_digest(self) -> str:
        data = self.body.encode()
        digest = SHA256.new(data=data).digest()
        base64 = b64encode(digest).decode("ascii")
        return "SHA-256=%s" % base64

    # noinspection PyUnresolvedReferences
    @signing_headers.default
    def _default_signing_headers(self) -> List[str]:
        return self.signing_attributes["headers"].strip().split(" ")

    # noinspection PyUnresolvedReferences
    @signing_string.default
    def _signing_string(self) -> str:
        components = []
        for name in self.signing_headers:
            if name == REQUEST_TARGET:
                components.append("%s: %s" % (REQUEST_TARGET, self.request_target))
            elif name == DIGEST:
                components.append("%s: %s" % (DIGEST, self.digest))
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


# pylint: disable=unused-argument:
def check_signature(context: SmartAppRequestContext, config: SmartAppDispatcherConfig, definition: SmartAppDefinition) -> None:
    """Verify the signature on a SmartApp request, raising SignatureError if invalid."""
    signature = SignatureContext(context=context, config=config, definition=definition)
    public_key = _retrieve_public_key(signature.key_url, signature.key_id)
    verify_rsa_sha256_signature(public_key, signature.signing_string, signature.signature)

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass:

"""
Shared functionality for REST clients.
"""
from typing import Optional, Union

import requests
from attrs import frozen


@frozen
class RestClientError(Exception):
    """An error invoking a RESTful API."""

    message: str
    request_body: Optional[Union[bytes, str]] = None
    response_body: Optional[str] = None


def raise_for_status(response: requests.Response) -> None:
    """Check response status, raising RestClientError for errors"""
    try:
        response.raise_for_status()
    except requests.models.HTTPError as e:
        raise RestClientError(
            message="Failed API call [%s %s]: %s" % (response.request.method, response.request.url, e),
            request_body=response.request.body,
            response_body=response.text,
        ) from e

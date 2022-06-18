# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass:

"""
Shared functionality for REST clients.
"""
from typing import Optional, Union

import requests
from attrs import frozen
from requests import ConnectionError as RequestsConnectionError
from requests import HTTPError
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential, wait_fixed

# This configures a single retry (2 total attempts), waiting 2 seconds before retrying
SINGLE_RETRY = retry(
    stop=stop_after_attempt(1),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((RequestsConnectionError, HTTPError)),
)

# This configures 5 retries (6 total attempts), waiting 0.25 seconds before first
# retry, and limiting the wait between retries to 2 seconds.
DECAYING_RETRY = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.25, max=2),
    retry=retry_if_exception_type((RequestsConnectionError, HTTPError)),
)


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

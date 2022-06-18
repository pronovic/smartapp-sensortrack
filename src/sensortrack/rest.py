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
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential


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


# This configures 4 retries (5 total attempts), waiting 0.25 seconds before first
# retry, and limiting the wait between retries to 2 seconds.
DECAYING_RETRY = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.25, max=2),
    retry=retry_if_exception_type((RestClientError, RequestsConnectionError, HTTPError)),
)

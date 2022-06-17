# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass:

"""
SmartThings API client
"""
from contextvars import ContextVar
from typing import Dict, Optional, Union

import requests
from attrs import field, frozen
from smartapp.converter import CONVERTER

from sensortrack.config import config


@frozen
class SmartThingsClientError(Exception):
    """An error invoking the SmartThings API."""

    message: str
    request_body: Optional[Union[bytes, str]] = None
    response_body: Optional[str] = None


@frozen(kw_only=True)
class Location:
    """Details about a location."""

    location_id: str
    name: str
    country_code: str
    latitude: Optional[float]
    longitude: Optional[float]
    temperature_scale: str  # either "F" or "C"
    time_zone_id: str
    locale: str


@frozen(kw_only=True)
class SmartThingsApiContext:

    token: str
    app_id: str
    location_id: str
    headers: Dict[str, str] = field(init=False)

    # noinspection PyUnresolvedReferences
    @headers.default
    def _default_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/vnd.smartthings+json;v=1",
            "Accept-Language": "en_US",
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % self.token,
        }


# Context managed by the SmartThings context manager
CONTEXT: ContextVar[SmartThingsApiContext] = ContextVar("CONTEXT")


class SmartThings:
    """Context manager for SmartThings API."""

    def __init__(self, token: str, app_id: str, location_id: str) -> None:
        self.context = CONTEXT.set(
            SmartThingsApiContext(
                token=token,
                app_id=app_id,
                location_id=location_id,
            )
        )

    def __enter__(self) -> None:
        return None

    def __exit__(self, _type, value, traceback) -> None:  # type: ignore[no-untyped-def]
        CONTEXT.reset(self.context)


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (config().smartthings.base_url, endpoint)


def _raise_for_status(response: requests.Response) -> None:
    """Check response status, raising SmartThingsClientError for errors"""
    try:
        response.raise_for_status()
    except requests.models.HTTPError as e:
        raise SmartThingsClientError(
            message="Failed SmartThings API call: %s" % e,
            request_body=response.request.body,
            response_body=response.text,
        ) from e


def _subscribe_to_event(capability: str, attribute: str) -> None:
    """Subscribe to an event by capability."""
    url = _url("/installedapps/%s/subscriptions" % CONTEXT.get().app_id)
    request = {
        "sourceType": "CAPABILITY",
        "capability": {
            "locationId": CONTEXT.get().location_id,
            "capability": capability,
            "attribute": attribute,
            "value": "*",
            "stateChangeOnly": True,
            "subscriptionName": "all-%s" % capability,  # note: limited to 36 characters
        },
    }
    response = requests.post(url=url, headers=CONTEXT.get().headers, json=request)
    _raise_for_status(response)


def retrieve_location() -> Location:
    """Retrieve details about the location."""
    url = _url("/locations/%s" % CONTEXT.get().location_id)
    response = requests.get(url=url, headers=CONTEXT.get().headers)
    _raise_for_status(response)
    return CONVERTER.from_json(response.text, Location)


def subscribe_to_temperature_events() -> None:
    """Subscribe to temperature events by capability."""
    _subscribe_to_event("temperatureMeasurement", "temperature")


def subscribe_to_humidity_events() -> None:
    """Subscribe to humidity events by capability."""
    _subscribe_to_event("relativeHumidityMeasurement", "humidity")

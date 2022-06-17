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
from sensortrack.weather import WeatherLocation

WEATHER_LOOKUP_TIMER = "weather-lookup"  # id of the weather lookup timer event


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

    def weather_eligible(self) -> bool:
        """Whether the location is eligible for NWS weather."""
        return self.country_code == "USA" and self.latitude is not None and self.longitude is not None

    def weather_location(self) -> WeatherLocation:
        """The weather location for this SmartThings location."""
        return WeatherLocation(
            location_id=self.location_id,
            latitude=self.latitude,  # type: ignore
            longitude=self.longitude,  # type: ignore
        )


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


def _delete_weather_lookup_timer() -> None:
    """Delete the weather lookup scheduled task."""
    url = _url("/installedapps/%s/schedules/%s" % (CONTEXT.get().app_id, WEATHER_LOOKUP_TIMER))
    response = requests.delete(url=url, headers=CONTEXT.get().headers)
    _raise_for_status(response)


def _create_weather_lookup_timer(location: Location, cron: str) -> None:
    """Create the weather lookup scheduled task."""
    # This is a little hackish, but encoding the location in the name lets us use SmartThings itself as a datastore
    name = location.weather_location().to_identifier()
    url = _url("/installedapps/%s/schedules/%s" % (CONTEXT.get().app_id, WEATHER_LOOKUP_TIMER))
    request = {"name": name, "cron": {"expression": cron, "timezone": "UTC"}}
    response = requests.post(url=url, headers=CONTEXT.get().headers, json=request)
    _raise_for_status(response)


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


def schedule_weather_lookup_timer(enabled: bool, cron: Optional[str]) -> None:
    """Create or replace the weather lookup timer for a given cron expression."""
    _delete_weather_lookup_timer()
    if enabled and cron:
        location = retrieve_location()
        if location.weather_eligible():
            _create_weather_lookup_timer(location, cron)


def subscribe_to_temperature_events() -> None:
    """Subscribe to temperature events by capability."""
    _subscribe_to_event("temperatureMeasurement", "temperature")


def subscribe_to_humidity_events() -> None:
    """Subscribe to humidity events by capability."""
    _subscribe_to_event("relativeHumidityMeasurement", "humidity")

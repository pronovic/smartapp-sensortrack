# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass:

"""
National Weather Service client.
"""
from __future__ import annotations  # so we can return a type from one of its own methods

from typing import Any, Dict, Optional, Tuple, Union

import jsonpath_ng
import pytemperature
import requests
from attrs import frozen

from sensortrack.config import config


@frozen
class WeatherClientError(Exception):
    """An error invoking the National Weather Service API."""

    message: str
    request_body: Optional[Union[bytes, str]] = None
    response_body: Optional[str] = None


@frozen(kw_only=True)
class WeatherLocation:
    location_id: str
    latitude: float
    longitude: float

    def to_identifier(self) -> str:
        """Encode a weather location into a string identifier."""
        return "weather/%s/%s/%s" % (self.location_id, self.latitude, self.longitude)

    @staticmethod
    def from_identifier(identifier: str) -> WeatherLocation:
        """Decode a weather location out of a string identifier."""
        location_id, latitude, longitude = identifier[len("weather/") :].split("/")
        return WeatherLocation(location_id=location_id, latitude=float(latitude), longitude=float(longitude))


def _extract_json(json: Dict[str, Any], jsonpath: str) -> Any:
    """Extract a value from a JSON document using jsonpath, returning None if it can't be parsed."""
    try:
        return jsonpath_ng.parse(jsonpath).find(json)[0].value
    except Exception as e:
        raise WeatherClientError("Could not find JSON attribute: %s" % jsonpath) from e


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (config().weather.base_url, endpoint)


def _raise_for_status(response: requests.Response) -> None:
    """Check response status, raising WeatherClientError for errors"""
    try:
        response.raise_for_status()
    except requests.models.HTTPError as e:
        raise WeatherClientError(
            message="Failed weather API call: %s" % e,
            request_body=response.request.body,
            response_body=response.text,
        ) from e


def _retrieve_station_url(latitude: float, longitude: float) -> str:
    """Retrieve the station URL for the closest station to a latitude and longitude."""
    url = _url("/points/%s,%s/stations" % (latitude, longitude))
    response = requests.get(url=url)
    _raise_for_status(response)
    return str(_extract_json(response.json(), "$.features[0].id"))


def _retrieve_latest_observation(station_url: str) -> Tuple[float, float]:
    """Return the latest (temperature, humidity) observation at a particular station, via its station URL."""
    # Temperature is always returned in degrees F, since this is a client only for U.S. based locations
    # It appears that the NWS API always returns temperatures in degrees C, so we need to convert that
    url = "%s/observations/latest" % station_url
    response = requests.get(url=url)
    _raise_for_status(response)
    temperature = pytemperature.c2f(_extract_json(response.json(), "$.properties.temperature.value"))
    humidity = round(float(_extract_json(response.json(), "$.properties.relativeHumidity.value")), 2)
    return temperature, humidity


def retrieve_current_conditions(location: WeatherLocation) -> Tuple[float, float]:
    """Retrieve current weather conditions a particular location."""
    # For design, see: https://github.com/weather-gov/api/discussions/215
    station_url = _retrieve_station_url(location.latitude, location.longitude)
    return _retrieve_latest_observation(station_url)

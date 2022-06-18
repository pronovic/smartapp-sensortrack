# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass:

"""
National Weather Service client.

In this interface, temperature is always returned in degrees F, since this client is for
use only with U.S. based locations.

The Swagger spec for the API says that all units must be valid WMO units.  The examples
I've seen always have "wmoUnit:degC" for temperature, and since there's no other
temperature unit in the WMO list, I'm assuming that it will always be C and it's safe to
always convert it to F.

In theory, SmartThings offers a WEATHER_EVENT that should have this same information,
and also for non-U.S. locations.  However, I can find no documentation about how to
actually subscribe to such a weather event.

See: https://weather-gov.github.io/api/general-faqs
     https://api.weather.gov/openapi.json
     http://codes.wmo.int/common/unit
     https://github.com/weather-gov/api/discussions/215
"""
from __future__ import annotations  # so we can return a type from one of its own methods

from typing import Any, Dict, Tuple

import jsonpath_ng
import pytemperature
import requests
from cachetools.func import ttl_cache

from sensortrack.config import config
from sensortrack.rest import DECAYING_RETRY, RestClientError, raise_for_status

STATION_TTL = 6 * 60 * 60  # cache station lookups for up to six hours


def _extract_json(json: Dict[str, Any], jsonpath: str) -> Any:
    """Extract a value from a JSON document using jsonpath, returning None if it can't be parsed."""
    try:
        return jsonpath_ng.parse(jsonpath).find(json)[0].value
    except Exception as e:
        raise RestClientError("Could not find JSON attribute: %s" % jsonpath) from e


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (config().weather.base_url, endpoint)


@DECAYING_RETRY
@ttl_cache(maxsize=128, ttl=STATION_TTL)
def _retrieve_station_url(latitude: float, longitude: float) -> str:
    """Retrieve the station URL for the closest station to a latitude and longitude."""
    url = _url("/points/%s,%s/stations" % (latitude, longitude))
    response = requests.get(url=url)
    raise_for_status(response)
    return str(_extract_json(response.json(), "$.features[0].id"))


@DECAYING_RETRY
def _retrieve_latest_observation(station_url: str) -> Tuple[float, float]:
    """Return the latest (temperature in F, humidity) observation at a particular station, via its station URL."""
    url = "%s/observations/latest" % station_url
    response = requests.get(url=url)
    raise_for_status(response)
    temperature = pytemperature.c2f(_extract_json(response.json(), "$.properties.temperature.value"))
    humidity = round(float(_extract_json(response.json(), "$.properties.relativeHumidity.value")), 2)
    return temperature, humidity


def retrieve_current_conditions(latitude: float, longitude: float) -> Tuple[float, float]:
    """Retrieve current weather conditions a particular lat/long location."""
    station_url = _retrieve_station_url(latitude, longitude)
    return _retrieve_latest_observation(station_url)

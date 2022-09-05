# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

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

from typing import Any, Dict, Optional, Tuple

import jsonpath_ng
import pytemperature
import requests

from sensortrack.config import config
from sensortrack.rest import DECAYING_RETRY, raise_for_status

_CLIENT_TIMEOUT_SEC = 5.0  # we want some fairly large timeout so that requests can't hang forever


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (config().weather.base_url, endpoint)


def _extract_float(json: Dict[str, Any], jsonpath: str) -> float:
    """Extract a float from a JSON document using jsonpath."""
    return jsonpath_ng.parse(jsonpath).find(json)[0].value  # type: ignore


def _extract_temperature(response: requests.Response) -> Optional[float]:
    """Extract temperature from the response, returning None if it can't be extracted."""
    try:
        return pytemperature.c2f(_extract_float(response.json(), "$.properties.temperature.value"))  # type: ignore
    except:  # pylint: disable=bare-except:
        return None


def _extract_humidity(response: requests.Response) -> Optional[float]:
    """Extract humidity from the response, returning None if it can't be extracted."""
    try:
        return round(float(_extract_float(response.json(), "$.properties.relativeHumidity.value")), 2)
    except:  # pylint: disable=bare-except:
        return None


@DECAYING_RETRY
def _retrieve_station_url(latitude: float, longitude: float) -> str:
    """Retrieve the station URL for the closest station to a latitude and longitude."""
    url = _url("/points/%s,%s/stations" % (latitude, longitude))
    response = requests.get(url=url, timeout=_CLIENT_TIMEOUT_SEC)
    raise_for_status(response)
    return str(_extract_float(response.json(), "$.features[0].id"))


@DECAYING_RETRY
def _retrieve_latest_observation(station_url: str) -> Tuple[Optional[float], Optional[float]]:
    """Return the latest (temperature in F, humidity) observation at a particular station, via its station URL."""
    url = "%s/observations/latest" % station_url
    response = requests.get(url=url, timeout=_CLIENT_TIMEOUT_SEC)
    raise_for_status(response)
    temperature = _extract_temperature(response)
    humidity = _extract_humidity(response)
    return temperature, humidity


def retrieve_current_conditions(latitude: float, longitude: float) -> Tuple[Optional[float], Optional[float]]:
    """Retrieve current weather conditions a particular lat/long location."""
    station_url = _retrieve_station_url(latitude, longitude)
    return _retrieve_latest_observation(station_url)

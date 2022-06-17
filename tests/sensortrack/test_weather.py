# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import json
import os
from unittest.mock import MagicMock, call, patch

import pytest
from requests.exceptions import HTTPError

from sensortrack.weather import WeatherClientError, WeatherLocation, _raise_for_status, retrieve_current_conditions
from tests.testutil import load_file

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestWeatherLocation:
    def test_weather_location(self):
        location = WeatherLocation(location_id="location", latitude=41.024654, longitude=-97.37219)
        assert location == location.from_identifier(location.to_identifier())


class TestPublicFunctions:
    @patch("sensortrack.weather._raise_for_status")
    @patch("sensortrack.weather.requests")
    @patch("sensortrack.weather.config")
    def test_retrieve_current_conditions(self, config, requests, raise_for_status):
        config.return_value = MagicMock(weather=MagicMock(base_url="https://base"))

        location = WeatherLocation(location_id="location", latitude="lat", longitude="long")

        stations = load_file(os.path.join(FIXTURE_DIR, "weather", "stations.json"))
        stations_url = "https://base/points/lat,long/stations"
        stations_response = MagicMock(json=MagicMock(return_value=json.loads(stations)))

        observations = load_file(os.path.join(FIXTURE_DIR, "weather", "observations.json"))
        observations_url = "https://api.weather.gov/stations/KALO/observations/latest"  # first station from JSON, which is closest
        observations_response = MagicMock(json=MagicMock(return_value=json.loads(observations)))

        requests.get = MagicMock(side_effect=[stations_response, observations_response])

        temperature, humidity = retrieve_current_conditions(location)

        requests.get.assert_has_calls([call(url=stations_url), call(url=observations_url)])
        raise_for_status.assert_has_calls([call(stations_response), call(observations_response)])

        assert temperature == 84.92  # expected result taken from Google, to sanity-check library
        assert humidity == 41.59


class TestPrivateFunctions:
    def test_raise_for_status(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.raise_for_status.side_effect = HTTPError("hello")
        with pytest.raises(WeatherClientError):
            _raise_for_status(response)

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import json
import os
from unittest.mock import MagicMock, call, patch

from requests import HTTPError

from sensortrack.weather import retrieve_current_conditions
from tests.testutil import load_file

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestPublicFunctions:
    @patch("sensortrack.weather.raise_for_status")
    @patch("sensortrack.weather.requests")
    @patch("sensortrack.weather.config")
    def test_retrieve_current_conditions(self, config, requests, raise_for_status):
        config.return_value = MagicMock(weather=MagicMock(base_url="https://base"))

        exception = HTTPError("hello")

        stations = load_file(os.path.join(FIXTURE_DIR, "weather", "stations.json"))
        stations_url = "https://base/points/12.3,45.6/stations"
        stations_response = MagicMock(json=MagicMock(return_value=json.loads(stations)))

        observations = load_file(os.path.join(FIXTURE_DIR, "weather", "observations.json"))
        observations_url = "https://api.weather.gov/stations/KALO/observations/latest"  # first station from JSON, which is closest
        observations_response = MagicMock(json=MagicMock(return_value=json.loads(observations)))

        # each exception is thrown, and that is handled by the retry annotation
        requests.get = MagicMock(
            side_effect=[exception, stations_response, exception, observations_response, observations_response]
        )

        # expected temperature taken from Google, to sanity-check library
        # the second call is partially cached, so we'll only do the observations lookup and not the station
        assert retrieve_current_conditions(latitude=12.3, longitude=45.6) == (84.92, 41.59)
        assert retrieve_current_conditions(latitude=12.3, longitude=45.6) == (84.92, 41.59)

        requests.get.assert_has_calls(
            [
                call(url=stations_url),
                call(url=stations_url),
                call(url=observations_url),
                call(url=observations_url),
                call(url=observations_url),
            ]
        )
        raise_for_status.assert_has_calls(
            [
                call(stations_response),
                call(observations_response),
                call(observations_response),
            ]
        )
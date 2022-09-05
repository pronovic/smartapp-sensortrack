# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import json
import os
from unittest.mock import MagicMock, call, patch

import pytest
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

        observations = load_file(os.path.join(FIXTURE_DIR, "weather", "observations", "valid.json"))
        observations_url = "https://api.weather.gov/stations/KALO/observations/latest"  # first station from JSON, which is closest
        observations_response = MagicMock(json=MagicMock(return_value=json.loads(observations)))

        # each exception is thrown, and that is handled by the retry annotation
        requests.get = MagicMock(
            side_effect=[exception, stations_response, exception, observations_response, observations_response]
        )

        # expected temperature taken from Google, to sanity-check library
        assert retrieve_current_conditions(latitude=12.3, longitude=45.6) == (84.92, 41.59)

        requests.get.assert_has_calls(
            [
                call(url=stations_url, timeout=5.0),
                call(url=stations_url, timeout=5.0),
                call(url=observations_url, timeout=5.0),
                call(url=observations_url, timeout=5.0),
            ]
        )
        raise_for_status.assert_has_calls(
            [
                call(stations_response),
                call(observations_response),
            ]
        )

    @patch("sensortrack.weather.raise_for_status")
    @patch("sensortrack.weather.requests")
    @patch("sensortrack.weather.config")
    @pytest.mark.parametrize(
        "input_file,expected",
        [
            ("invalid.json", (None, None)),
            ("missing.json", (None, None)),
            ("null.json", (None, None)),
        ],
    )
    def test_retrieve_current_conditions_bad_data(self, config, requests, raise_for_status, input_file, expected):
        config.return_value = MagicMock(weather=MagicMock(base_url="https://base"))

        stations = load_file(os.path.join(FIXTURE_DIR, "weather", "stations.json"))
        stations_url = "https://base/points/12.3,45.6/stations"
        stations_response = MagicMock(json=MagicMock(return_value=json.loads(stations)))

        observations = load_file(os.path.join(FIXTURE_DIR, "weather", "observations", input_file))
        observations_url = "https://api.weather.gov/stations/KALO/observations/latest"  # first station from JSON, which is closest
        observations_response = MagicMock(json=MagicMock(return_value=json.loads(observations)))

        requests.get = MagicMock(side_effect=[stations_response, observations_response])

        # expected temperature taken from Google, to sanity-check library
        assert retrieve_current_conditions(latitude=12.3, longitude=45.6) == expected

        requests.get.assert_has_calls(
            [
                call(url=stations_url, timeout=5.0),
                call(url=observations_url, timeout=5.0),
            ]
        )
        raise_for_status.assert_has_calls(
            [
                call(stations_response),
                call(observations_response),
            ]
        )

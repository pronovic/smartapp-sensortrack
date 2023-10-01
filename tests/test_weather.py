# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import MagicMock, patch

import pytest
import responses
from responses import matchers
from responses.registries import OrderedRegistry

from sensortrack.rest import RestDataError
from sensortrack.weather import retrieve_current_conditions
from tests.testutil import load_file

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
TIMEOUT_MATCHER = matchers.request_kwargs_matcher({"timeout": 5.0})


class TestPublicFunctions:
    @patch("sensortrack.weather.config")
    def test_retrieve_current_conditions(self, config):
        config.return_value = MagicMock(weather=MagicMock(base_url="https://base"))
        with responses.RequestsMock(registry=OrderedRegistry) as r:
            r.get(
                url="https://base/points/12.3,45.6/stations",
                status=500,
                match=[TIMEOUT_MATCHER],
            )
            r.get(
                url="https://base/points/12.3,45.6/stations",
                status=200,
                body=load_file(os.path.join(FIXTURE_DIR, "weather/stations", "stations.json")),
                match=[TIMEOUT_MATCHER],
            )
            r.get(
                url="https://api.weather.gov/stations/KALO/observations/latest",  # first station from JSON, which is closest
                status=500,
                match=[TIMEOUT_MATCHER],
            )
            r.get(
                url="https://api.weather.gov/stations/KALO/observations/latest",  # first station from JSON, which is closest
                status=200,
                body=load_file(os.path.join(FIXTURE_DIR, "weather", "observations", "valid.json")),
                match=[TIMEOUT_MATCHER],
            )
            # expected temperature taken from Google, to sanity-check library
            assert retrieve_current_conditions(latitude=12.3, longitude=45.6) == (84.92, 41.59)
            assert len(r.calls) == 4  # one retry and one success for each endpoint

    @patch("sensortrack.weather.config")
    def test_retrieve_current_conditions_bad_stations(self, config):
        config.return_value = MagicMock(weather=MagicMock(base_url="https://base"))
        with responses.RequestsMock(registry=OrderedRegistry) as r:
            r.get(
                url="https://base/points/12.3,45.6/stations",
                status=200,
                body=load_file(os.path.join(FIXTURE_DIR, "weather/stations", "empty.json")),
                match=[TIMEOUT_MATCHER],
            )
            with pytest.raises(RestDataError):
                assert retrieve_current_conditions(latitude=12.3, longitude=45.6) == "xxx"

    @patch("sensortrack.weather.config")
    @pytest.mark.parametrize(
        "input_file,expected",
        [
            ("invalid.json", (None, None)),
            ("missing.json", (None, None)),
            ("null.json", (None, None)),
        ],
    )
    def test_retrieve_current_conditions_bad_data(self, config, input_file, expected):
        config.return_value = MagicMock(weather=MagicMock(base_url="https://base"))
        with responses.RequestsMock(registry=OrderedRegistry) as r:
            r.get(
                url="https://base/points/12.3,45.6/stations",
                status=200,
                body=load_file(os.path.join(FIXTURE_DIR, "weather/stations", "stations.json")),
                match=[TIMEOUT_MATCHER],
            )
            r.get(
                url="https://api.weather.gov/stations/KALO/observations/latest",  # first station from JSON, which is closest
                status=200,
                body=load_file(os.path.join(FIXTURE_DIR, "weather", "observations", input_file)),
                match=[TIMEOUT_MATCHER],
            )
            # expected temperature taken from Google, to sanity-check library
            assert retrieve_current_conditions(latitude=12.3, longitude=45.6) == expected

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import MagicMock, call, patch

import pytest
from requests.exceptions import HTTPError

from sensortrack.smartthings import (
    Location,
    SmartThings,
    SmartThingsClientError,
    _raise_for_status,
    retrieve_location,
    schedule_weather_lookup_timer,
    subscribe_to_humidity_events,
    subscribe_to_temperature_events,
)
from sensortrack.weather import WeatherLocation
from tests.testutil import load_file

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

CONFIG = MagicMock(smartthings=MagicMock(base_url="https://base"))
HEADERS = {
    "Accept": "application/vnd.smartthings+json;v=1",
    "Accept-Language": "en_US",
    "Content-Type": "application/json",
    "Authorization": "Bearer token",
}


class TestLocation:
    def test_location_weather_eligible(self):
        assert Location(location_id="", name="", country_code="USA", latitude=1, longitude=2).weather_eligible() is True
        assert Location(location_id="", name="", country_code="GB", latitude=1, longitude=2).weather_eligible() is False
        assert Location(location_id="", name="", country_code="USA", latitude=None, longitude=2).weather_eligible() is False
        assert Location(location_id="", name="", country_code="USA", latitude=1, longitude=None).weather_eligible() is False

    def test_location_weather_location(self):
        assert Location(
            location_id="l",
            name="",
            country_code="USA",
            latitude=1,
            longitude=2,
        ).weather_location() == WeatherLocation(
            location_id="l",
            latitude=1,
            longitude=2,
        )


class TestPrivateFunctions:
    def test_raise_for_status(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.raise_for_status.side_effect = HTTPError("hello")
        with pytest.raises(SmartThingsClientError):
            _raise_for_status(response)


@patch("sensortrack.smartthings._raise_for_status")
@patch("sensortrack.smartthings.requests")
@patch("sensortrack.smartthings.config")
class TestPublicFunctions:
    @pytest.mark.parametrize(
        "function,capability,attribute",
        [
            (subscribe_to_temperature_events, "temperatureMeasurement", "temperature"),
            (subscribe_to_humidity_events, "relativeHumidityMeasurement", "humidity"),
        ],
    )
    def test_subscribe_to_events(self, config, requests, raise_for_status, function, capability, attribute):
        config.return_value = CONFIG

        url = "https://base/installedapps/app/subscriptions"
        request = {
            "sourceType": "CAPABILITY",
            "capability": {
                "locationId": "location",
                "capability": capability,
                "attribute": attribute,
                "value": "*",
                "stateChangeOnly": True,
                "subscriptionName": "all-%s" % capability,
            },
        }

        response = MagicMock()
        requests.post = MagicMock(return_value=response)

        with SmartThings(token="token", app_id="app", location_id="location"):
            function()

        requests.post.assert_called_once_with(url=url, headers=HEADERS, json=request)
        raise_for_status.assert_called_once_with(response)

    def test_retrieve_location(self, config, requests, raise_for_status):
        config.return_value = CONFIG

        data = load_file(os.path.join(FIXTURE_DIR, "smartthings", "location.json"))
        expected = Location(
            location_id="15526d0a-XXXX-XXXX-XXXX-b6247aacbbb2",
            name="My House",
            country_code="USA",
            latitude=41.024654,
            longitude=-97.37219,
        )

        url = "https://base/locations/location"

        response = MagicMock(text=data)
        requests.get = MagicMock(return_value=response)

        with SmartThings(token="token", app_id="app", location_id="location"):
            retrieved = retrieve_location()
            assert retrieved == expected

        requests.get.assert_called_once_with(url=url, headers=HEADERS)
        raise_for_status.assert_called_once_with(response)

    @pytest.mark.parametrize(
        "enabled,cron",
        [
            (False, "cron"),
            (True, None),
        ],
    )
    def test_schedule_weather_lookup_timer_disabled(self, config, requests, raise_for_status, enabled, cron):
        config.return_value = CONFIG

        delete_response = MagicMock()

        requests.delete = MagicMock(return_value=delete_response)
        requests.get = MagicMock()
        url = "https://base/installedapps/app/schedules/weather-lookup"

        with SmartThings(token="token", app_id="app", location_id="location"):
            schedule_weather_lookup_timer(enabled, cron)

        # not enabled, so we delete only
        requests.delete.assert_called_once_with(url=url, headers=HEADERS)
        requests.get.assert_not_called()
        raise_for_status.assert_called_once_with(delete_response)

    @patch("sensortrack.smartthings.retrieve_location")
    def test_schedule_weather_lookup_timer_not_eligible(self, retrieve, config, requests, raise_for_status):
        config.return_value = CONFIG

        location = MagicMock()
        location.weather_eligible = MagicMock(return_value=False)
        retrieve.return_value = location

        delete_response = MagicMock()

        requests.delete = MagicMock(return_value=delete_response)
        requests.post = MagicMock()
        url = "https://base/installedapps/app/schedules/weather-lookup"

        with SmartThings(token="token", app_id="app", location_id="location"):
            schedule_weather_lookup_timer(True, "expr")

        # enabled but not eligible, so we delete only
        requests.delete.assert_called_once_with(url=url, headers=HEADERS)
        requests.post.assert_not_called()
        raise_for_status.assert_called_once_with(delete_response)

    @patch("sensortrack.smartthings.retrieve_location")
    def test_schedule_weather_lookup_timer_enabled(self, retrieve, config, requests, raise_for_status):
        config.return_value = CONFIG

        weather = MagicMock()
        weather.to_identifier = MagicMock(return_value="identifier")
        location = MagicMock()
        location.weather_eligible = MagicMock(return_value=True)
        location.weather_location = MagicMock(return_value=weather)
        retrieve.return_value = location

        delete_response = MagicMock()
        post_response = MagicMock()

        requests.delete = MagicMock(return_value=delete_response)
        requests.post = MagicMock(return_value=post_response)
        url = "https://base/installedapps/app/schedules/weather-lookup"

        request = {"name": "identifier", "cron": {"expression": "expr", "timezone": "UTC"}}

        with SmartThings(token="token", app_id="app", location_id="location"):
            schedule_weather_lookup_timer(True, "expr")

        # eligible, so we delete and re-add
        requests.delete.assert_called_once_with(url=url, headers=HEADERS)
        requests.post.assert_called_once_with(url=url, headers=HEADERS, json=request)
        raise_for_status.assert_has_calls([call(delete_response), call(post_response)])

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import MagicMock, call, patch

import pytest

from sensortrack.smartthings import (
    Location,
    SmartThings,
    retrieve_location,
    schedule_weather_lookup_timer,
    subscribe_to_humidity_events,
    subscribe_to_temperature_events,
)
from tests.testutil import load_file

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

CONFIG = MagicMock(smartthings=MagicMock(base_url="https://base"))
HEADERS = {
    "Accept": "application/vnd.smartthings+json;v=1",
    "Accept-Language": "en_US",
    "Content-Type": "application/json",
    "Authorization": "Bearer token",
}

REQUEST = MagicMock()
REQUEST.token = MagicMock(return_value="token")
REQUEST.app_id = MagicMock(return_value="app")
REQUEST.location_id = MagicMock(return_value="location")


@patch("sensortrack.smartthings.raise_for_status")
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

        with SmartThings(request=REQUEST):
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

        # the second call is cached
        with SmartThings(request=REQUEST):
            assert retrieve_location() == expected
            assert retrieve_location() == expected

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
        url = "https://base/installedapps/app/schedules/identifier"

        with SmartThings(request=REQUEST):
            schedule_weather_lookup_timer("identifier", enabled, cron)

        # not enabled, so we delete only
        requests.delete.assert_called_once_with(url=url, headers=HEADERS)
        raise_for_status.assert_called_once_with(delete_response)

    def test_schedule_weather_lookup_timer_enabled(self, config, requests, raise_for_status):
        config.return_value = CONFIG

        delete_response = MagicMock()
        post_response = MagicMock()

        requests.delete = MagicMock(return_value=delete_response)
        requests.post = MagicMock(return_value=post_response)
        url = "https://base/installedapps/app/schedules/identifier"

        request = {"name": "identifier", "cron": {"expression": "expr", "timezone": "UTC"}}

        with SmartThings(request=REQUEST):
            schedule_weather_lookup_timer("identifier", True, "expr")

        # enabled, so we delete and re-add
        requests.delete.assert_called_once_with(url=url, headers=HEADERS)
        requests.post.assert_called_once_with(url=url, headers=HEADERS, json=request)
        raise_for_status.assert_has_calls([call(delete_response), call(post_response)])

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError

from sensortrack.smartthings import (
    Location,
    SmartThings,
    SmartThingsClientError,
    _raise_for_status,
    _subscribe_to_event,
    retrieve_location,
    subscribe_to_humidity_events,
    subscribe_to_temperature_events,
)
from tests.testutil import load_file

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

HEADERS = {
    "Accept": "application/vnd.smartthings+json;v=1",
    "Accept-Language": "en_US",
    "Content-Type": "application/json",
    "Authorization": "Bearer token",
}


class TestPublicFunctions:
    @patch("sensortrack.smartthings._subscribe_to_event")
    def test_subscribe_to_temperature_events(self, subscribe):
        subscribe_to_temperature_events()
        subscribe.assert_called_once_with("temperatureMeasurement", "temperature")

    @patch("sensortrack.smartthings._subscribe_to_event")
    def test_subscribe_to_humidity_events(self, subscribe):
        subscribe_to_humidity_events()
        subscribe.assert_called_once_with("relativeHumidityMeasurement", "humidity")

    @patch("sensortrack.smartthings._raise_for_status")
    @patch("sensortrack.smartthings.requests")
    @patch("sensortrack.smartthings.config")
    def test_retrieve_location(self, config, requests, raise_for_status):
        config.return_value = MagicMock(smartthings=MagicMock(base_url="https://base"))

        path = os.path.join("smartthings", "location.json")
        data = load_file(os.path.join(FIXTURE_DIR, path))

        expected = Location(
            location_id="15526d0a-XXXX-XXXX-XXXX-b6247aacbbb2",
            name="My House",
            country_code="USA",
            latitude=41.024654,
            longitude=-97.37219,
            temperature_scale="F",
            time_zone_id="America/Chicago",
            locale="en-US",
        )

        url = "https://base/locations/location"

        response = MagicMock(text=data)
        requests.get = MagicMock(return_value=response)

        with SmartThings(token="token", app_id="app", location_id="location"):
            retrieved = retrieve_location()
            assert retrieved == expected

        requests.get.assert_called_once_with(url=url, headers=HEADERS)
        raise_for_status.assert_called_once_with(response)


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
    def test_subscribe_to_event(self, config, requests, raise_for_status):
        config.return_value = MagicMock(smartthings=MagicMock(base_url="https://base"))

        url = "https://base/installedapps/app/subscriptions"
        request = {
            "sourceType": "CAPABILITY",
            "capability": {
                "locationId": "location",
                "capability": "capability",
                "attribute": "attribute",
                "value": "*",
                "stateChangeOnly": True,
                "subscriptionName": "all-capability",
            },
        }

        response = MagicMock()
        requests.post = MagicMock(return_value=response)

        with SmartThings(token="token", app_id="app", location_id="location"):
            _subscribe_to_event(capability="capability", attribute="attribute")

        requests.post.assert_called_once_with(url=url, headers=HEADERS, json=request)
        raise_for_status.assert_called_once_with(response)

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError

from sensortrack.smartthings import (
    SmartThings,
    SmartThingsClientError,
    _raise_for_status,
    _subscribe_to_event,
    subscribe_to_humidity_events,
    subscribe_to_temperature_events,
)


class TestPublicFunctions:
    @patch("sensortrack.smartthings._subscribe_to_event")
    def test_subscribe_to_temperature_events(self, subscribe):
        subscribe_to_temperature_events()
        subscribe.assert_called_once_with("temperatureMeasurement", "temperature")

    @patch("sensortrack.smartthings._subscribe_to_event")
    def test_subscribe_to_humidity_events(self, subscribe):
        subscribe_to_humidity_events()
        subscribe.assert_called_once_with("relativeHumidityMeasurement", "humidity")


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
        headers = {
            "Accept": "application/vnd.smartthings+json;v=1",
            "Accept-Language": "en_US",
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }
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

        requests.post.assert_called_once_with(url=url, headers=headers, json=request)
        raise_for_status.assert_called_once_with(response)

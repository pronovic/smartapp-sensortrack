# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from typing import Dict, Pattern
from unittest.mock import MagicMock, patch

import pytest
import responses
from responses import matchers
from responses.registries import OrderedRegistry

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
HEADERS: Dict[str, str | Pattern[str]] = {
    "Accept": "application/vnd.smartthings+json;v=1",
    "Accept-Language": "en_US",
    "Content-Type": "application/json",
    "Authorization": "Bearer token",
}

REQUEST = MagicMock()
REQUEST.token = MagicMock(return_value="token")
REQUEST.app_id = MagicMock(return_value="app")
REQUEST.location_id = MagicMock(return_value="location")

TIMEOUT_MATCHER = matchers.request_kwargs_matcher({"timeout": 5.0})
HEADERS_MATCHER = matchers.header_matcher(HEADERS)


@patch("sensortrack.smartthings.config")
class TestPublicFunctions:
    @pytest.mark.parametrize(
        "function,capability,attribute",
        [
            (subscribe_to_temperature_events, "temperatureMeasurement", "temperature"),
            (subscribe_to_humidity_events, "relativeHumidityMeasurement", "humidity"),
        ],
    )
    def test_subscribe_to_events(self, config, function, capability, attribute):
        config.return_value = CONFIG
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
        with responses.RequestsMock(registry=OrderedRegistry) as r:
            r.post(
                url="https://base/installedapps/app/subscriptions",
                status=500,
                json=request,
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            r.post(
                url="https://base/installedapps/app/subscriptions",
                status=200,
                json=request,
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            with SmartThings(request=REQUEST):
                function()
            assert len(r.calls) == 2  # one for the the failed attempt, one for the retry

    def test_retrieve_location(self, config):
        config.return_value = CONFIG
        with responses.RequestsMock(registry=OrderedRegistry) as r:
            r.get(
                url="https://base/locations/location",
                status=500,
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            r.get(
                url="https://base/locations/location",
                status=200,
                body=load_file(os.path.join(FIXTURE_DIR, "smartthings", "location.json")),
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            with SmartThings(request=REQUEST):
                assert retrieve_location() == Location(
                    location_id="15526d0a-XXXX-XXXX-XXXX-b6247aacbbb2",
                    name="My House",
                    country_code="USA",
                    latitude=41.024654,
                    longitude=-97.37219,
                )
            assert len(r.calls) == 2  # one for the the failed attempt, one for the retry

    @pytest.mark.parametrize(
        "enabled,cron",
        [
            (False, "cron"),
            (True, None),
        ],
    )
    def test_schedule_weather_lookup_timer_disabled(self, config, enabled, cron):
        config.return_value = CONFIG
        with responses.RequestsMock(registry=OrderedRegistry) as r:
            r.delete(
                url="https://base/installedapps/app/schedules/identifier",
                status=500,
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            r.delete(
                url="https://base/installedapps/app/schedules/identifier",
                status=200,
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            with SmartThings(request=REQUEST):
                schedule_weather_lookup_timer("identifier", enabled, cron)
            assert len(r.calls) == 2  # one for the the failed attempt, one for the retry

    def test_schedule_weather_lookup_timer_enabled(self, config):
        config.return_value = CONFIG
        request = {"name": "identifier", "cron": {"expression": "expr", "timezone": "UTC"}}
        with responses.RequestsMock(registry=OrderedRegistry) as r:
            r.delete(
                url="https://base/installedapps/app/schedules/identifier",
                status=200,
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            r.post(
                url="https://base/installedapps/app/schedules",
                status=500,
                json=request,
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            r.post(
                url="https://base/installedapps/app/schedules",
                status=200,
                json=request,
                match=[TIMEOUT_MATCHER, HEADERS_MATCHER],
            )
            with SmartThings(request=REQUEST):
                schedule_weather_lookup_timer("identifier", True, "expr")
            assert len(r.calls) == 3  # one for the delete, one for the failed post, one for the retry

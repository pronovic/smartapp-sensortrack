# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,protected-access:

from typing import List
from unittest.mock import MagicMock, patch

import pytest
from influxdb_client import Point
from smartapp.interface import EventType

from sensortrack.handler import WEATHER_LOOKUP_TIMER, EventHandler

CORRELATION_ID = "xxx"


@pytest.fixture
def handler() -> EventHandler:
    return EventHandler()


class TestEventHandler:
    def test_handle_confirmation(self, handler):
        handler.handle_confirmation(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    def test_handle_configuration(self, handler):
        handler.handle_configuration(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    def test_handle_uninstall(self, handler):
        handler.handle_uninstall(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    def test_handle_oauth_callback(self, handler):
        handler.handle_oauth_callback(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    @patch("sensortrack.handler.subscribe_to_temperature_events")
    @patch("sensortrack.handler.subscribe_to_humidity_events")
    @patch("sensortrack.handler.schedule_weather_lookup_timer")
    @patch("sensortrack.handler.SmartThings")
    @pytest.mark.parametrize(
        "enabled,expr,provided",
        [
            (True, "expr", "expr"),
            (False, "expr", None),
        ],
    )
    def test_handle_install(self, smartthings, schedule, humidity, temperature, handler, enabled, expr, provided):
        request = MagicMock()
        request.as_bool = MagicMock(return_value=enabled)
        request.as_str = MagicMock(return_value=expr)

        handler.handle_install(CORRELATION_ID, request)

        smartthings.assert_called_once_with(request=request)
        schedule.assert_called_once_with(WEATHER_LOOKUP_TIMER, enabled, provided)
        temperature.assert_called_once()
        humidity.assert_called_once()
        request.as_bool.assert_called_once_with("retrieve-weather-enabled")
        if enabled:
            request.as_str.assert_called_once_with("retrieve-weather-cron")
        else:
            request.as_str.assert_not_called()

    @patch("sensortrack.handler.subscribe_to_temperature_events")
    @patch("sensortrack.handler.subscribe_to_humidity_events")
    @patch("sensortrack.handler.schedule_weather_lookup_timer")
    @patch("sensortrack.handler.SmartThings")
    @pytest.mark.parametrize(
        "enabled,expr,provided",
        [
            (True, "expr", "expr"),
            (False, "expr", None),
        ],
    )
    def test_handle_update(self, smartthings, schedule, humidity, temperature, handler, enabled, expr, provided):
        request = MagicMock()
        request.as_bool = MagicMock(return_value=enabled)
        request.as_str = MagicMock(return_value=expr)
        request.update_data.as_bool = MagicMock(return_value=enabled)
        request.update_data.as_str = MagicMock(return_value=expr)

        handler.handle_update(CORRELATION_ID, request)

        smartthings.assert_called_once_with(request=request)
        schedule.assert_called_once_with(WEATHER_LOOKUP_TIMER, enabled, provided)
        temperature.assert_not_called()
        humidity.assert_not_called()
        request.as_bool.assert_called_once_with("retrieve-weather-enabled")
        if enabled:
            request.as_str.assert_called_once_with("retrieve-weather-cron")
        else:
            request.as_str.assert_not_called()

    @patch("sensortrack.handler.InfluxDBClient")
    @patch("sensortrack.handler.config")
    def test_handle_event(self, config, influxdb, handler):
        request = MagicMock()
        request.event_data = MagicMock()
        request.event_data.filter = MagicMock(
            return_value=[
                {
                    "locationId": "l",
                    "deviceId": "d",
                    "attribute": "t",
                    "value": 23.7,
                },
            ]
        )

        config.return_value = MagicMock(
            influxdb=MagicMock(
                url="url",
                org="org",
                token="token",
                bucket="bucket",
            ),
        )

        # Ugh, the stubbing for a context manager is hideous
        client = MagicMock()
        client.__enter__ = MagicMock()
        client.__enter__.return_value = MagicMock()
        client.__enter__.return_value.write_api = MagicMock()
        client.__enter__.return_value.write_api.return_value = MagicMock()
        client.__enter__.return_value.write_api.return_value.write = MagicMock()
        influxdb.return_value = client

        handler.handle_event(CORRELATION_ID, request)

        influxdb.assert_called_once_with(url="url", org="org", token="token")
        request.event_data.filter.assert_called_once_with(event_type=EventType.DEVICE_EVENT)

        # there's no equality available on the Point class, so we have to do this the hard way
        (_, kwargs) = client.__enter__.return_value.write_api.return_value.write.call_args
        bucket: str = kwargs["bucket"]
        points: List[Point] = kwargs["record"]
        assert bucket == "bucket"
        assert len(points) == 1
        assert len(points[0]._tags) == 2
        assert len(points[0]._fields) == 1
        assert points[0]._name == "sensor"
        assert points[0]._tags["location"] == "l"
        assert points[0]._tags["device"] == "d"
        assert points[0]._fields["t"] == 23.7

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,protected-access:

from typing import List
from unittest.mock import MagicMock, call, patch

import pytest
from influxdb_client import Point
from smartapp.interface import EventType

from sensortrack.handler import IS_WEATHER_LOOKUP, WEATHER_LOOKUP, EventHandler

CORRELATION_ID = "xxx"


@pytest.fixture
def handler() -> EventHandler:
    return EventHandler()


class TestEventHandler:
    @pytest.mark.parametrize(
        "event,expected",
        [
            ({}, False),
            ({"name": None}, False),
            ({"name": ""}, False),
            ({"name": "bogus"}, False),
            ({"name": WEATHER_LOOKUP}, True),
        ],
    )
    def test_is_weather_lookup(self, event, expected):
        assert IS_WEATHER_LOOKUP(event) is expected

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
        schedule.assert_called_once_with(WEATHER_LOOKUP, enabled, provided)
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
        schedule.assert_called_once_with(WEATHER_LOOKUP, enabled, provided)
        temperature.assert_not_called()
        humidity.assert_not_called()
        request.as_bool.assert_called_once_with("retrieve-weather-enabled")
        if enabled:
            request.as_str.assert_called_once_with("retrieve-weather-cron")
        else:
            request.as_str.assert_not_called()

    @patch("sensortrack.handler.InfluxDBClient")
    @patch("sensortrack.handler.config")
    def test_handle_event_device(self, config, influxdb, handler):
        request = MagicMock()
        request.event_data = MagicMock()
        request.event_data.filter = MagicMock()

        # There are two calls to filter(), one for TIMER_EVENT and one for DEVICE_EVENT.
        # This test case validates the device event behavior, so we return an empty list of timer events.
        request.event_data.filter.side_effect = [
            [],
            [
                {
                    "locationId": "l",
                    "deviceId": "d",
                    "attribute": "t",
                    "value": 23.7,
                },
            ],
        ]

        config.return_value = MagicMock(
            influxdb=MagicMock(
                url="url",
                org="org",
                token="token",
                bucket="bucket",
            ),
        )

        # Ugh, the stubbing for a context manager is hideous
        write = MagicMock()
        influxdb.return_value = MagicMock(
            __enter__=MagicMock(
                return_value=MagicMock(
                    write_api=MagicMock(
                        return_value=MagicMock(write=write),
                    ),
                ),
            ),
        )

        handler.handle_event(CORRELATION_ID, request)

        influxdb.assert_called_once_with(url="url", org="org", token="token")
        request.event_data.filter.assert_has_calls(
            [
                call(event_type=EventType.TIMER_EVENT, predicate=IS_WEATHER_LOOKUP),
                call(event_type=EventType.DEVICE_EVENT),
            ]
        )

        # there's no equality available on the Point class, so we have to do this the hard way
        (_, kwargs) = write.call_args
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

    @patch("sensortrack.handler.retrieve_current_conditions")
    @patch("sensortrack.handler.retrieve_location")
    @patch("sensortrack.handler.SmartThings")
    @patch("sensortrack.handler.InfluxDBClient")
    @patch("sensortrack.handler.config")
    @pytest.mark.parametrize(
        "location,eligible",
        [
            (MagicMock(location_id="l", country_code="USA", latitude=12.3, longitude=45.6), True),
            (MagicMock(location_id="l", country_code=None, latitude=12.3, longitude=45.6), False),
            (MagicMock(location_id="l", country_code="", latitude=12.3, longitude=45.6), False),
            (MagicMock(location_id="l", country_code="bogus", latitude=12.3, longitude=45.6), False),
            (MagicMock(location_id="l", country_code="USA", latitude=None, longitude=45.6), False),
            (MagicMock(location_id="l", country_code="USA", latitude=12.3, longitude=None), False),
        ],
    )
    def test_handle_event_timer(
        self, config, influxdb, smartthings, retrieve_location, retrieve_current_conditions, handler, location, eligible
    ):
        request = MagicMock()
        request.event_data = MagicMock()
        request.event_data.filter = MagicMock()

        # There are two calls to filter(), one for TIMER_EVENT and one for DEVICE_EVENT.
        # This test case validates the timer event behavior, so we return an empty list of device events.
        # There multiple timer events, but we'll still only do the lookup once
        request.event_data.filter.side_effect = [
            [
                {"name": "lookup"},
                {"name": "lookup"},
            ],
            [],
        ]

        config.return_value = MagicMock(
            influxdb=MagicMock(
                url="url",
                org="org",
                token="token",
                bucket="bucket",
            ),
        )

        retrieve_location.return_value = location
        retrieve_current_conditions.return_value = 78.9, 10.2

        # Ugh, the stubbing for a context manager is hideous
        write = MagicMock()
        influxdb.return_value = MagicMock(
            __enter__=MagicMock(
                return_value=MagicMock(
                    write_api=MagicMock(
                        return_value=MagicMock(write=write),
                    ),
                ),
            ),
        )

        handler.handle_event(CORRELATION_ID, request)

        request.event_data.filter.assert_has_calls(
            [
                call(event_type=EventType.TIMER_EVENT, predicate=IS_WEATHER_LOOKUP),
                call(event_type=EventType.DEVICE_EVENT),
            ]
        )

        influxdb.assert_called_once_with(url="url", org="org", token="token")
        smartthings.assert_called_once_with(request=request)
        retrieve_location.assert_called_once()
        if eligible:
            retrieve_current_conditions.assert_called_once_with(12.3, 45.6)
        else:
            retrieve_current_conditions.assert_not_called()

        # there's no equality available on the Point class, so we have to do this the hard way
        (_, kwargs) = write.call_args
        bucket: str = kwargs["bucket"]
        points: List[Point] = kwargs["record"]
        assert bucket == "bucket"
        if eligible:
            assert len(points) == 1
            assert len(points[0]._tags) == 1
            assert len(points[0]._fields) == 2
            assert points[0]._name == "weather"
            assert points[0]._tags["location"] == "l"
            assert points[0]._fields["temperature"] == 78.9
            assert points[0]._fields["humidity"] == 10.2
        else:
            assert len(points) == 0

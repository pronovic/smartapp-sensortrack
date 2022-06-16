# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,protected-access:

from typing import List
from unittest.mock import MagicMock, patch

import pytest
from influxdb_client import Point

from sensortrack.handler import EventHandler

CORRELATION_ID = "xxx"


@pytest.fixture
def handler() -> EventHandler:
    return EventHandler()


class TestEventHandler:
    def test_handle_confirmation(self, handler):
        handler.handle_confirmation(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    def test_handle_configuration(self, handler):
        handler.handle_configuration(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    def test_handle_update(self, handler):
        handler.handle_update(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    def test_handle_uninstall(self, handler):
        handler.handle_uninstall(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    def test_handle_oauth_callback(self, handler):
        handler.handle_oauth_callback(CORRELATION_ID, MagicMock())  # just make sure it doesn't blow up

    @patch("sensortrack.handler.subscribe_to_temperature_events")
    @patch("sensortrack.handler.subscribe_to_humidity_events")
    @patch("sensortrack.handler.SmartThings")
    def test_handle_install(self, smartthings, humidity, temperature, handler):
        request = MagicMock(
            install_data=MagicMock(
                auth_token="token",
                installed_app=MagicMock(installed_app_id="app", location_id="location"),
            )
        )
        handler.handle_install(CORRELATION_ID, request)
        smartthings.assert_called_once_with(token="token", app_id="app", location_id="location")
        temperature.assert_called_once()
        humidity.assert_called_once()

    @patch("sensortrack.handler.InfluxDBClient")
    @patch("sensortrack.handler.config")
    def test_handle_event(self, config, influxdb, handler):
        request = MagicMock(
            event_data=MagicMock(
                events=[
                    MagicMock(
                        device_event=None,  # represents any other kind of event
                    ),
                    MagicMock(
                        device_event=MagicMock(
                            location_id="l",
                            device_id="d",
                            attribute="t",
                            value=23.7,
                        ),
                    ),
                ]
            )
        )
        config.return_value = MagicMock(
            influxdb=MagicMock(
                url="url",
                org="org",
                token="token",
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

        # there's no equality available on the Point class, so we have to do this the hard way
        (_, kwargs) = client.__enter__.return_value.write_api.return_value.write.call_args
        bucket: str = kwargs["bucket"]
        points: List[Point] = kwargs["record"]
        assert bucket == "sensors"
        assert len(points) == 1
        assert len(points[0]._tags) == 2
        assert len(points[0]._fields) == 1
        assert points[0]._name == "sensor"
        assert points[0]._tags["location"] == "l"
        assert points[0]._tags["device"] == "d"
        assert points[0]._fields["t"] == 23.7

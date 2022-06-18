# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass,too-many-locals:

"""
SmartApp event handler.
"""
import logging
from typing import Callable, List, Optional, Union

from influxdb_client import InfluxDBClient, Point
from smartapp.interface import (
    ConfigurationRequest,
    ConfirmationRequest,
    EventRequest,
    EventType,
    InstallRequest,
    OauthCallbackRequest,
    SmartAppEventHandler,
    UninstallRequest,
    UpdateRequest,
)

from sensortrack.config import config
from sensortrack.smartthings import (
    SmartThings,
    schedule_weather_lookup_timer,
    subscribe_to_humidity_events,
    subscribe_to_temperature_events,
)


# noinspection PyMethodMayBeStatic
class EventHandler(SmartAppEventHandler):

    """SmartApp event handler."""

    def handle_confirmation(self, correlation_id: Optional[str], request: ConfirmationRequest) -> None:
        """Handle a CONFIRMATION lifecycle request"""
        pass  # no action needed for this event, the standard dispatcher does everything that's needed

    def handle_configuration(self, correlation_id: Optional[str], request: ConfigurationRequest) -> None:
        """Handle a CONFIGURATION lifecycle request."""
        pass  # no action needed for this event, the standard dispatcher does everything that's needed

    def handle_install(self, correlation_id: Optional[str], request: InstallRequest) -> None:
        """Handle an INSTALL lifecycle request."""
        self._handle_config_refresh(correlation_id, request, subscribe=True)

    def handle_update(self, correlation_id: Optional[str], request: UpdateRequest) -> None:
        """Handle an UPDATE lifecycle request."""
        # Note: no need to subscribe to device events, because the CAPABILITY subscription should already cover all devices
        self._handle_config_refresh(correlation_id, request, subscribe=False)

    def handle_uninstall(self, correlation_id: Optional[str], request: UninstallRequest) -> None:
        """Handle an UNINSTALL lifecycle request."""
        pass  # no action needed for this event, since subscriptions and schedules have already been deleted

    def handle_oauth_callback(self, correlation_id: Optional[str], request: OauthCallbackRequest) -> None:
        """Handle an OAUTH_CALLBACK lifecycle request."""
        pass  # no action needed for this event, since we don't use any special oauth integration

    def handle_event(self, correlation_id: Optional[str], request: EventRequest) -> None:
        """Handle an EVENT lifecycle request."""
        url = config().influxdb.url
        org = config().influxdb.org
        token = config().influxdb.token
        bucket = config().influxdb.bucket
        with InfluxDBClient(url=url, org=org, token=token) as client:
            write_api = client.write_api()

            def writer(points: List[Point]) -> None:
                write_api.write(bucket=bucket, record=points)
                logging.debug("[%s] Completed persisting %d point(s) of data", correlation_id, len(points))

            self._handle_sensor_events(request, writer)

    def _handle_config_refresh(
        self, correlation_id: Optional[str], request: Union[InstallRequest, UpdateRequest], subscribe: bool
    ) -> None:
        """Handle configuration refresh for an INSTALL or UPDATE event."""
        token = request.token()
        app_id = request.app_id()
        location_id = request.location_id()
        weather_enabled = request.as_bool("retrieve-weather-enabled")
        weather_cron = request.as_str("retrieve-weather-cron") if weather_enabled else None
        with SmartThings(token=token, app_id=app_id, location_id=location_id):
            schedule_weather_lookup_timer(weather_enabled, weather_cron)
            logging.info("[%s] Completed scheduling weather lookup timer for %s", correlation_id, app_id)
            if subscribe:
                subscribe_to_temperature_events()
                subscribe_to_humidity_events()
                logging.info("[%s] Completed subscribing to device events for app %s", correlation_id, app_id)

    def _handle_sensor_events(self, request: EventRequest, writer: Callable[[List[Point]], None]) -> None:
        """Handle received events from temperature and humidity sensors."""
        points = []
        for event in request.event_data.filter(event_type=EventType.DEVICE_EVENT):
            location_id = event["locationId"]
            device_id = event["deviceId"]
            attribute = event["attribute"]  # "temperature" or "humidity"
            measurement = round(float(event["value"]), 2)
            point = Point("sensor").tag("location", location_id).tag("device", device_id).field(attribute, measurement)
            points.append(point)
        writer(points)

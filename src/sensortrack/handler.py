# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass,too-many-locals:

"""
SmartApp event handler.
"""
import logging
from typing import List, Optional, Union

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
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
    retrieve_location,
    schedule_weather_lookup_timer,
    subscribe_to_humidity_events,
    subscribe_to_temperature_events,
)
from sensortrack.weather import retrieve_current_conditions

WEATHER_LOOKUP = "weather-lookup"  # name/id of the weather lookup timer event
IS_WEATHER_LOOKUP = lambda event: "name" in event and event["name"] == WEATHER_LOOKUP


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
            points = []  # type: List[Point]
            self._handle_weather_lookup_events(request, points)
            self._handle_sensor_events(request, points)
            client.write_api(write_options=SYNCHRONOUS).write(bucket=bucket, record=points)
            logging.debug("[%s] Completed persisting %d point(s) of data", correlation_id, len(points))

    def _handle_config_refresh(
        self, correlation_id: Optional[str], request: Union[InstallRequest, UpdateRequest], subscribe: bool
    ) -> None:
        """Handle configuration refresh for an INSTALL or UPDATE event."""
        weather_enabled = request.as_bool("retrieve-weather-enabled")
        weather_cron = request.as_str("retrieve-weather-cron") if weather_enabled else None
        with SmartThings(request=request):
            schedule_weather_lookup_timer(WEATHER_LOOKUP, weather_enabled, weather_cron)
            logging.info("[%s] Completed scheduling weather lookup timer", correlation_id)
            if subscribe:
                subscribe_to_temperature_events()
                subscribe_to_humidity_events()
                logging.info("[%s] Completed subscribing to device events", correlation_id)

    def _handle_weather_lookup_events(self, request: EventRequest, points: List[Point]) -> None:
        """Handle weather event lookup timer events, appending any points to be persisted to InfluxDB."""
        if request.event_data.filter(event_type=EventType.TIMER_EVENT, predicate=IS_WEATHER_LOOKUP):
            with SmartThings(request=request):
                location = retrieve_location()
                if location.country_code == "USA" and location.latitude is not None and location.longitude is not None:
                    temperature, humidity = retrieve_current_conditions(location.latitude, location.longitude)
                    points.append(
                        Point("weather")
                        .tag("location", location.location_id)
                        .field("temperature", temperature)
                        .field("humidity", humidity)
                    )

    def _handle_sensor_events(self, request: EventRequest, points: List[Point]) -> None:
        """Handle received events from sensors, appending any points to be persisted to InfluxDB."""
        for event in request.event_data.filter(event_type=EventType.DEVICE_EVENT):
            location_id = event["locationId"]
            device_id = event["deviceId"]
            attribute = event["attribute"]  # "temperature" or "humidity"
            measurement = round(float(event["value"]), 2)
            points.append(Point("sensor").tag("location", location_id).tag("device", device_id).field(attribute, measurement))

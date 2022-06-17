# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass,too-many-locals:

"""
SmartApp event handler.
"""
import logging
from typing import Optional

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
from sensortrack.smartthings import SmartThings, subscribe_to_humidity_events, subscribe_to_temperature_events


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
        token = request.install_data.auth_token
        app_id = request.install_data.installed_app.installed_app_id
        location_id = request.install_data.installed_app.location_id
        with SmartThings(token=token, app_id=app_id, location_id=location_id):
            subscribe_to_temperature_events()
            subscribe_to_humidity_events()
            logging.info("Completed subscribing to device events for app %s", app_id)

    def handle_update(self, correlation_id: Optional[str], request: UpdateRequest) -> None:
        """Handle an UPDATE lifecycle request."""
        pass  # no action needed for this event, since we are already subscribed to all devices by capability

    def handle_uninstall(self, correlation_id: Optional[str], request: UninstallRequest) -> None:
        """Handle an UNINSTALL lifecycle request."""
        pass  # no action needed for this event, subscriptions and schedules have already been deleted

    def handle_oauth_callback(self, correlation_id: Optional[str], request: OauthCallbackRequest) -> None:
        """Handle an OAUTH_CALLBACK lifecycle request."""
        pass  # no action needed for this event, we don't use any special oauth integration

    def handle_event(self, correlation_id: Optional[str], request: EventRequest) -> None:
        """Handle an EVENT lifecycle request."""
        url = config().influxdb.url
        org = config().influxdb.org
        token = config().influxdb.token
        bucket = config().influxdb.bucket
        logging.info("URL: %s, org=%s, token=%s", url, org, token)
        with InfluxDBClient(url=url, org=org, token=token) as client:
            points = []
            write_api = client.write_api()
            for event in request.event_data.events:
                if event.event_type == EventType.DEVICE_EVENT and event.device_event:
                    location_id = event.device_event["locationId"]
                    device_id = event.device_event["deviceId"]
                    attribute = event.device_event["attribute"]  # "temperature" or "humidity"
                    measurement = round(float(event.device_event["value"]), 2)  # the actual value, seems to be a float
                    point = Point("sensor").tag("location", location_id).tag("device", device_id).field(attribute, measurement)
                    points.append(point)
            write_api.write(bucket=bucket, record=points)
            logging.debug("Completed persisting %d point(s) of data", len(points))

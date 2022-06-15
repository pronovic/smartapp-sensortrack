# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from sensortrack.dispatcher import DISPATCHER
from sensortrack.handler import EventHandler


class TestDispatcher:
    def test_dispatcher(self):
        # Check all configuration, since some of these values are important for security
        assert DISPATCHER.config.check_signatures is True
        assert DISPATCHER.config.clock_skew_sec == 300
        assert DISPATCHER.config.keyserver_url == "https://key.smartthings.com"
        assert DISPATCHER.config.log_json is False

        # Spot-check the SmartApp definition, just to be sure it loaded ok from disk
        assert DISPATCHER.definition.id == "sensor-track"
        assert DISPATCHER.definition.name == "Sensor Tracking"

        # Confirm that event handler is set as expected
        assert isinstance(DISPATCHER.event_handler, EventHandler)

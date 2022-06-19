# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock, patch

import pytest
from smartapp.interface import SmartAppDispatcherConfig

from sensortrack.dispatcher import dispatcher, reset
from sensortrack.handler import EventHandler


class TestDispatcher:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Reset singleton before and after tests."""
        reset()
        yield
        reset()

    @patch("sensortrack.dispatcher.config")
    def test_dispatcher(self, config):
        config.return_value = MagicMock(dispatcher=SmartAppDispatcherConfig())

        # Check that we loaded dispatcher configuration from global state
        assert dispatcher().config is not None

        # Spot-check the SmartApp definition, just to be sure it loaded ok from disk
        assert dispatcher().definition.id == "sensortrack"
        assert dispatcher().definition.name == "Sensor Tracking"

        # Confirm that event handler is set as expected
        assert isinstance(dispatcher().event_handler, EventHandler)

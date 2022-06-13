# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
SmartApp dispatcher.
"""
import importlib.resources

from smartapp.converter import CONVERTER
from smartapp.dispatcher import SmartAppDefinition, SmartAppDispatcher

from .handler import EventHandler

_CONFIG_PACKAGE = "sensortrack.data"
_CONFIG_FILE = "definition.yaml"


def _load_definition() -> SmartAppDefinition:
    with importlib.resources.open_text(_CONFIG_PACKAGE, _CONFIG_FILE) as f:
        return CONVERTER.from_yaml(f.read(), SmartAppDefinition)


DEFINITION = _load_definition()
EVENT_HANDLER = EventHandler()
DISPATCHER = SmartAppDispatcher(definition=DEFINITION, event_handler=EVENT_HANDLER)

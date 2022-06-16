# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
SmartApp dispatcher.
"""
import importlib.resources
from typing import Optional

from smartapp.converter import CONVERTER
from smartapp.dispatcher import SmartAppDispatcher
from smartapp.interface import SmartAppDefinition

from .config import config
from .handler import EventHandler

_DATA_PACKAGE = "sensortrack.data"
_DEFINITION_FILE = "definition.yaml"  # definition of the SmartApp


def _load_definition() -> SmartAppDefinition:
    with importlib.resources.open_text(_DATA_PACKAGE, _DEFINITION_FILE) as f:
        return CONVERTER.from_yaml(f.read(), SmartAppDefinition)


_DISPATCHER: Optional[SmartAppDispatcher] = None
_DEFINITION = _load_definition()


def reset() -> None:
    """Reset the config singleton, forcing it to be reloaded when next used."""
    global _DISPATCHER  # pylint: disable=global-statement
    _DISPATCHER = None


def dispatcher() -> SmartAppDispatcher:
    """Return a dispatcher, loading configuration once and caching the instance."""
    global _DISPATCHER  # pylint: disable=global-statement
    if _DISPATCHER is None:
        _DISPATCHER = SmartAppDispatcher(
            config=config().dispatcher,
            definition=_DEFINITION,
            event_handler=EventHandler(),
        )
    return _DISPATCHER

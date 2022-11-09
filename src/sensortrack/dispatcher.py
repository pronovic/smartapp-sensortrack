# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
SmartApp dispatcher.
"""
from typing import Optional

from importlib_resources import files
from smartapp.converter import CONVERTER
from smartapp.dispatcher import SmartAppDispatcher
from smartapp.interface import SmartAppDefinition

import sensortrack.data

from .config import config
from .handler import EventHandler

_DEFINITION_FILE = "definition.yaml"  # definition of the SmartApp


def _load_definition() -> SmartAppDefinition:
    yaml = files(sensortrack.data).joinpath(_DEFINITION_FILE).read_text()
    return CONVERTER.from_yaml(yaml, SmartAppDefinition)


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

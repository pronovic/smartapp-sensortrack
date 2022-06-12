# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=line-too-long:

"""
EVENT phase in the SmartApp lifecycle.
"""

# I can't find any official documentation about the event structure, only the code referenced below.
# See: https://github.com/SmartThingsCommunity/smartapp-sdk-nodejs/blob/f1ef97ec9c6dc270ba744197b842c6632c778987/lib/lifecycle-events.d.ts

from abc import ABC
from typing import Any, Dict, List

from attrs import frozen

from sensortrack.lifecycle.common import LifecyclePhase, LifecycleRequest
from sensortrack.lifecycle.installedapp import InstalledApp

PHASE = LifecyclePhase.EVENT

# TODO: implement individual event type classes
# TODO: like with other parts of the interface, this will need some sort of custom unstructure mechanism


@frozen
class Event(ABC):
    """Abstract parent class for all types of events."""


@frozen
class EventData:
    """Event data."""

    auth_token: str
    installed_app: InstalledApp
    events: List[Event]


@frozen
class EventRequest(LifecycleRequest):
    """Request for EVENT phase"""

    event_data: EventData
    settings: Dict[str, Any]


@frozen
class EventResponse:
    """Response for EVENT phase"""

    event_data: Dict[str, Any] = {}  # always empty in the response

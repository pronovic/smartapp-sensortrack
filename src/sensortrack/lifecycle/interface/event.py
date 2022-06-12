# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=line-too-long:

"""
EVENT phase in the SmartApp lifecycle.
"""

# I can't find any official documentation about the event structure, only the code referenced below.
# So, the structure below mostly mirrors the definitions within the AppEvent namespace, except I've excluded the enums
# See: https://github.com/SmartThingsCommunity/smartapp-sdk-nodejs/blob/f1ef97ec9c6dc270ba744197b842c6632c778987/lib/lifecycle-events.d.ts

from enum import Enum
from typing import Any, Dict, List, Optional

from attrs import frozen
from pendulum.datetime import DateTime

from sensortrack.lifecycle.interface.installedapp import InstalledApp
from sensortrack.lifecycle.interface.lifecycle import AbstractRequest, LifecyclePhase

PHASE = LifecyclePhase.EVENT

# TODO: like with other parts of the interface, this will need some sort of custom unstructure mechanism


class EventType(Enum):
    """Event types."""

    DEVICE_EVENT = "DEVICE_EVENT"
    TIMER_EVENT = "TIMER_EVENT"
    DEVICE_COMMANDS_EVENT = "DEVICE_COMMANDS_EVENT"
    DEVICE_LIFECYCLE_EVENT = "DEVICE_LIFECYCLE_EVENT"
    DEVICE_HEALTH_EVENT = "DEVICE_HEALTH_EVENT"
    HUB_HEALTH_EVENT = "HUB_HEALTH_EVENT"
    MODE_EVENT = "MODE_EVENT"
    SECURITY_ARM_STATE_EVENT = "SECURITY_ARM_STATE_EVENT"
    INSTALLED_APP_LIFECYCLE_EVENT = "INSTALLED_APP_LIFECYCLE_EVENT"


@frozen
class DeviceEvent:
    """A device event."""

    event_id: str
    location_id: str
    device_id: str
    component_id: str
    capability: str
    attribute: str
    value: Any  # TODO: exactly what do we get here?  Seems like this is too generic?
    value_type: str
    state_change: bool
    data: Dict[str, Any]
    subscription_name: str


class DeviceLifecycleEvent:
    """A device lifecycle event."""

    lifecycle: str
    event_id: str
    location_id: str
    device_id: str
    device_name: str
    principal: str


@frozen
class DeviceHealthEvent:
    event_id: str
    location_id: str
    device_id: str
    hub_id: str
    status: str
    reason: str


@frozen
class HubHealthEvent:
    event_id: str
    location_id: str
    hub_id: str
    status: str
    reason: str


@frozen
class DeviceCommand:
    component_id: str
    capability: str
    command: str
    arguments: List[Any]  # TODO: exactly what do we get here?  Seems like this is too generic?


@frozen
class DeviceCommandsEvent:
    event_id: str
    device_id: str
    profile_id: str
    external_id: str
    commands: List[DeviceCommand]


@frozen
class ModeEvent:
    event_id: str
    location_id: str
    mode_id: str


@frozen
class TimerEvent:
    event_id: str
    name: str
    type: str
    time: DateTime
    expression: str


@frozen
class SceneLifecycleEvent:
    lifecycle: str
    event_id: str
    location_id: str
    scene_id: str


@frozen
class SecurityArmStateEvent:
    event_id: str
    location_id: str
    arm_state: str
    optional_arguments: Dict[str, Any]


@frozen
class Event:
    """Holds the triggered event, one of several different attributes depending on event type."""

    event_time: DateTime
    event_type: EventType
    device_event: Optional[DeviceEvent] = None
    device_lifecycle_event: Optional[DeviceLifecycleEvent] = None
    device_health_event: Optional[DeviceHealthEvent] = None
    device_commands_event: Optional[DeviceCommandsEvent] = None
    mode_event: Optional[ModeEvent] = None
    timer_event: Optional[TimerEvent] = None
    scene_lifecycle_event: Optional[SceneLifecycleEvent] = None
    security_arm_state_event: Optional[SecurityArmStateEvent] = None


@frozen
class EventData:
    """Event data."""

    auth_token: str
    installed_app: InstalledApp
    events: List[Event]


@frozen
class EventRequest(AbstractRequest):
    """Request for EVENT phase"""

    event_data: EventData
    settings: Dict[str, Any]


@frozen
class EventResponse:
    """Response for EVENT phase"""

    event_data: Dict[str, Any] = {}  # always empty in the response

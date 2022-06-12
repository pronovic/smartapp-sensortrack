# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Common code for the SmartApp lifecycle.
"""
from abc import ABC
from enum import Enum
from typing import Dict, List, Optional

from attrs import frozen


class ConfigValueType(str, Enum):
    DEVICE = "deviceConfig"
    STRING = "stringConfig"


@frozen
class ConfigValue(ABC):
    """Abstract parent class for all types of config values."""

    value_type: ConfigValueType


@frozen
class DeviceValue:
    device_id: str
    component_id: str


@frozen
class DeviceConfigValue(ConfigValue):
    """DEVICE configuration value."""

    device_config: DeviceValue


@frozen
class StringValue:
    value: str


@frozen
class StringConfigValue(ConfigValue):
    """STRING configuration value."""

    string_config: StringValue


@frozen
class InstalledApp:
    """Installed application."""

    installed_app_id: str
    location_id: str
    config: Dict[str, List[ConfigValue]]
    previous_config: Optional[Dict[str, List[ConfigValue]]] = None
    permissions: List[str] = []

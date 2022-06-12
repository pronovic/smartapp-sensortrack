# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
CONFIGURATION phase in the SmartApp lifecycle.
"""

from abc import ABC
from enum import Enum
from typing import Any, Dict, List, Optional

from attrs import frozen

from sensortrack.lifecycle.common import LifecycleRequest


class ConfigPhase(Enum):
    INITIALIZE = "INITIALIZE"
    PAGE = "PAGE"


class ConfigSettingType(Enum):
    DEVICE = "DEVICE"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    ENUM = "ENUM"
    LINK = "LINK"
    PAGE = "PAGE"
    IMAGE = "IMAGE"
    ICON = "ICON"
    TIME = "TIME"
    PARAGRAPH = "PARAGRAPH"
    EMAIL = "EMAIL"
    DECIMAL = "DECIMAL"
    NUMBER = "NUMBER"
    PHONE = "PHONE"
    OAUTH = "OAUTH"


class BooleanValue(str, Enum):
    TRUE = "true"
    FALSE = "false"


# TODO: we are going to need some sort of custom structure mechanism for ConfigSetting,
#       because there's no good way for cattrs to understand how to create the correct
#       subclass.


@frozen
class ConfigSetting(ABC):
    """Abstract parent class for all types of config settings."""

    id: str
    name: str
    description: str
    type: ConfigSettingType
    required: bool


@frozen
class DeviceSetting(ConfigSetting):
    """A DEVICE setting."""

    multiple: bool
    capabilities: List[str]
    permissions: List[str]


@frozen
class TextSetting(ConfigSetting):
    """A TEXT setting."""

    defaultValue: str


@frozen
class BooleanSetting(ConfigSetting):
    """A BOOLEAN setting."""

    defaultValue: BooleanValue


@frozen
class EnumOption:
    id: str
    name: str


@frozen
class GroupedEnumOption:
    name: str
    options: List[EnumOption]


@frozen
class EnumSetting(ConfigSetting):
    """An ENUM setting."""

    multiple: bool
    options: List[EnumOption]
    grouped_options: Optional[List[GroupedEnumOption]] = None


@frozen
class LinkSetting(ConfigSetting):
    """A LINK setting."""

    url: str
    image: str


@frozen
class PageSetting(ConfigSetting):
    """A PAGE setting."""

    page: str
    image: str


@frozen
class ImageSetting(ConfigSetting):
    """An IMAGE setting."""

    image: str


@frozen
class IconSetting(ConfigSetting):
    """An ICON setting."""

    image: str


@frozen
class TimeSetting(ConfigSetting):
    """A TIME setting."""


@frozen
class ParagraphSetting(ConfigSetting):
    """A PARAGRAPH setting."""

    defaultValue: str


@frozen
class EmailSetting(ConfigSetting):
    """An EMAIL setting."""


@frozen
class DecimalSetting(ConfigSetting):
    """A DECIMAL setting."""


@frozen
class NumberSetting(ConfigSetting):
    """A NUMBER setting."""


@frozen
class PhoneSetting(ConfigSetting):
    """A PHONE setting."""


@frozen
class OauthSetting(ConfigSetting):
    """An OAUTH setting."""

    browser: bool
    url_template: str


@frozen
class ConfigInit:
    """Initialization data."""

    name: str
    description: str
    id: str
    permissions: List[str]
    first_page_id: str


@frozen
class ConfigData:
    """Configuration data."""

    installed_app_id: str
    phase: ConfigPhase
    page_id: str
    previous_page_id: str
    config: Dict[str, Any]


@frozen
class ConfigSection:
    """A section within a configuration page."""

    name: str
    settings: List[ConfigSetting]


@frozen
class ConfigPage:
    """A page of configuration data for the CONFIGURATION phase."""

    page_id: str
    name: str
    next_page_id: str
    previous_page_id: str
    complete: bool
    sections: List[ConfigSection]


@frozen
class ConfigRequest(LifecycleRequest):
    """Request for CONFIGURATION phase"""

    configuration_data: ConfigData
    settings: Dict[str, Any]


@frozen
class ConfigInitResponse:
    """Response for CONFIGURATION/INITIALIZE phase"""

    initialize: ConfigInit


@frozen
class ConfigPageResponse:
    """Response for CONFIGURATION/PAGE phase"""

    page: ConfigPage

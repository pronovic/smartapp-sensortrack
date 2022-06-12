# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=line-too-long:

"""
The SmartApp lifecycle interface.
"""

# See: https://developer-preview.smartthings.com/docs/connected-services/lifecycles/
#      https://developer-preview.smartthings.com/docs/connected-services/configuration/

# I can't find any official documentation about the event structure, only the Javascript code referenced below.
# So, the structure below mostly mirrors the definitions within the AppEvent namespace, except I've excluded most enums.
# Also, there is a scene lifecycle class (but no event id), and an installed app event id (but no class), so I've ignored those.
# See: https://github.com/SmartThingsCommunity/smartapp-sdk-nodejs/blob/f1ef97ec9c6dc270ba744197b842c6632c778987/lib/lifecycle-events.d.ts

from abc import ABC
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from attrs import field, frozen
from pendulum.datetime import DateTime


class LifecyclePhase(Enum):
    """Lifecycle phases."""

    CONFIRMATION = "CONFIRMATION"
    CONFIGURATION = "CONFIGURATION"
    INSTALL = "INSTALL"
    UPDATE = "UPDATE"
    EVENT = "EVENT"
    OAUTH_CALLBACK = "OAUTH_CALLBACK"
    UNINSTALL = "UNINSTALL"


class ConfigValueType(Enum):
    """Types of config values."""

    DEVICE = "DEVICE"
    STRING = "STRING"


class ConfigPhase(Enum):
    """Sub-phases within the CONFIGURATION phase."""

    INITIALIZE = "INITIALIZE"
    PAGE = "PAGE"


class ConfigSettingType(Enum):
    """Types of config settings."""

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


class EventType(Enum):
    """Supported event types."""

    DEVICE_EVENT = "DEVICE_EVENT"
    DEVICE_LIFECYCLE_EVENT = "DEVICE_LIFECYCLE_EVENT"
    DEVICE_HEALTH_EVENT = "DEVICE_HEALTH_EVENT"
    HUB_HEALTH_EVENT = "HUB_HEALTH_EVENT"
    DEVICE_COMMANDS_EVENT = "DEVICE_COMMANDS_EVENT"
    MODE_EVENT = "MODE_EVENT"
    TIMER_EVENT = "TIMER_EVENT"
    SECURITY_ARM_STATE_EVENT = "SECURITY_ARM_STATE_EVENT"


class BooleanValue(str, Enum):
    """String boolean values."""

    TRUE = "true"
    FALSE = "false"


@frozen
class AbstractRequest(ABC):
    """Abstract parent class for all types of lifecycle requests."""

    lifecycle: LifecyclePhase
    execution_id: str
    locale: str
    version: str


@frozen
class AbstractSetting(ABC):
    """Abstract parent class for all types of config settings."""

    id: str
    name: str
    description: str
    required: bool


@frozen
class DeviceSetting(AbstractSetting):
    """A DEVICE setting."""

    multiple: bool
    capabilities: List[str]
    permissions: List[str]
    type: ConfigSettingType = ConfigSettingType.DEVICE


@frozen
class TextSetting(AbstractSetting):
    """A TEXT setting."""

    defaultValue: str
    type: ConfigSettingType = ConfigSettingType.TEXT


@frozen
class BooleanSetting(AbstractSetting):
    """A BOOLEAN setting."""

    defaultValue: BooleanValue
    type: ConfigSettingType = ConfigSettingType.BOOLEAN


@frozen
class EnumOption:
    """An option within an ENUM setting"""

    id: str
    name: str


@frozen
class EnumOptionGroup:
    """A group of options within an ENUM setting"""

    name: str
    options: List[EnumOption]


@frozen
class EnumSetting(AbstractSetting):
    """An ENUM setting."""

    multiple: bool
    options: List[EnumOption]
    grouped_options: Optional[List[EnumOptionGroup]] = None
    type: ConfigSettingType = ConfigSettingType.ENUM


@frozen
class LinkSetting(AbstractSetting):
    """A LINK setting."""

    url: str
    image: str
    type: ConfigSettingType = ConfigSettingType.LINK


@frozen
class PageSetting(AbstractSetting):
    """A PAGE setting."""

    page: str
    image: str
    type: ConfigSettingType = ConfigSettingType.PAGE


@frozen
class ImageSetting(AbstractSetting):
    """An IMAGE setting."""

    image: str
    type: ConfigSettingType = ConfigSettingType.IMAGE


@frozen
class IconSetting(AbstractSetting):
    """An ICON setting."""

    image: str
    type: ConfigSettingType = ConfigSettingType.ICON


@frozen
class TimeSetting(AbstractSetting):
    """A TIME setting."""

    type: ConfigSettingType = ConfigSettingType.TIME


@frozen
class ParagraphSetting(AbstractSetting):
    """A PARAGRAPH setting."""

    defaultValue: str
    type: ConfigSettingType = ConfigSettingType.PARAGRAPH


@frozen
class EmailSetting(AbstractSetting):
    """An EMAIL setting."""

    type: ConfigSettingType = ConfigSettingType.EMAIL


@frozen
class DecimalSetting(AbstractSetting):
    """A DECIMAL setting."""

    type: ConfigSettingType = ConfigSettingType.DECIMAL


@frozen
class NumberSetting(AbstractSetting):
    """A NUMBER setting."""

    type: ConfigSettingType = ConfigSettingType.NUMBER


@frozen
class PhoneSetting(AbstractSetting):
    """A PHONE setting."""

    type: ConfigSettingType = ConfigSettingType.PHONE


@frozen
class OauthSetting(AbstractSetting):
    """An OAUTH setting."""

    browser: bool
    url_template: str
    type: ConfigSettingType = ConfigSettingType.OAUTH


ConfigSetting = Union[
    DeviceSetting,
    TextSetting,
    BooleanSetting,
    EnumSetting,
    LinkSetting,
    PageSetting,
    ImageSetting,
    IconSetting,
    TimeSetting,
    ParagraphSetting,
    EmailSetting,
    DecimalSetting,
    NumberSetting,
    PhoneSetting,
    OauthSetting,
]


@frozen
class DeviceValue:
    device_id: str
    component_id: str


@frozen
class DeviceConfigValue:
    """DEVICE configuration value."""

    device_config: DeviceValue
    value_type: ConfigValueType = ConfigValueType.DEVICE


@frozen
class StringValue:
    value: str


@frozen
class StringConfigValue:
    """STRING configuration value."""

    string_config: StringValue
    value_type: ConfigValueType = ConfigValueType.STRING


ConfigValue = Union[
    DeviceConfigValue,
    StringConfigValue,
]


@frozen
class InstalledApp:
    """Installed application."""

    installed_app_id: str
    location_id: str
    config: Dict[str, List[ConfigValue]]
    permissions: List[str] = field(factory=list)


@frozen
class DeviceEvent:
    """A device event."""

    subscription_name: str
    event_id: str
    location_id: str
    device_id: str
    component_id: str
    capability: str
    attribute: str
    value: str
    state_change: bool
    data: Optional[Dict[str, Any]] = None


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
class SecurityArmStateEvent:
    event_id: str
    location_id: str
    arm_state: str
    optional_arguments: Dict[str, Any]


@frozen
class Event:
    """Holds the triggered event, one of several different attributes depending on event type."""

    event_type: EventType
    event_time: Optional[DateTime] = None
    device_event: Optional[DeviceEvent] = None
    device_lifecycle_event: Optional[DeviceLifecycleEvent] = None
    device_health_event: Optional[DeviceHealthEvent] = None
    device_commands_event: Optional[DeviceCommandsEvent] = None
    mode_event: Optional[ModeEvent] = None
    timer_event: Optional[TimerEvent] = None
    security_arm_state_event: Optional[SecurityArmStateEvent] = None


@frozen
class ConfirmationData:
    """Confirmation data."""

    app_id: str
    confirmation_url: str


@frozen
class ConfigInit:
    """Initialization data."""

    name: str
    description: str
    id: str
    permissions: List[str]
    first_page_id: str


@frozen
class ConfigRequestData:
    """Configuration data provided on the request."""

    installed_app_id: str
    phase: ConfigPhase
    page_id: str
    previous_page_id: str
    config: Dict[str, List[ConfigValue]]


@frozen
class ConfigInitData:
    """Configuration data provided in an INITIALIZATION response."""

    initialize: ConfigInit


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
    next_page_id: Optional[str]
    previous_page_id: Optional[str]
    complete: bool
    sections: List[ConfigSection]


@frozen
class ConfigPageData:
    """Configuration data provided in an PAGE response."""

    page: ConfigPage


@frozen
class InstallData:
    """Install data."""

    auth_token: str
    refresh_token: str
    installed_app: InstalledApp


@frozen
class UpdateData:
    """Update data."""

    auth_token: str
    refresh_token: str
    installed_app: InstalledApp
    previous_config: Optional[Dict[str, List[ConfigValue]]] = None
    previous_permissions: List[str] = field(factory=list)


@frozen
class UninstallData:
    """Install data."""

    installed_app: InstalledApp


@frozen
class OauthCallbackData:
    installed_app_id: str
    url_path: str


@frozen
class EventData:
    """Event data."""

    auth_token: str
    installed_app: InstalledApp
    events: List[Event]


@frozen
class ConfirmationRequest(AbstractRequest):
    """Request for CONFIRMATION phase"""

    app_id: str
    confirmation_data: ConfirmationData
    settings: Dict[str, Any] = field(factory=dict)


@frozen
class ConfirmationResponse:
    """Response for CONFIRMATION phase"""

    target_url: str


@frozen
class ConfigurationRequest(AbstractRequest):
    """Request for CONFIGURATION phase"""

    configuration_data: ConfigRequestData
    settings: Dict[str, Any] = field(factory=dict)


@frozen
class ConfigurationInitResponse:
    """Response for CONFIGURATION/INITIALIZE phase"""

    configuration_data: ConfigInitData


@frozen
class ConfigurationPageResponse:
    """Response for CONFIGURATION/PAGE phase"""

    configuration_data: ConfigPageData


@frozen
class InstallRequest(AbstractRequest):
    """Request for INSTALL phase"""

    install_data: InstallData
    settings: Dict[str, Any] = field(factory=dict)


@frozen
class InstallResponse:
    """Response for INSTALL phase"""

    install_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


@frozen
class UpdateRequest(AbstractRequest):
    """Request for UPDATE phase"""

    update_data: UpdateData
    settings: Dict[str, Any] = field(factory=dict)


@frozen
class UpdateResponse:
    """Response for UPDATE phase"""

    update_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


@frozen
class UninstallRequest(AbstractRequest):
    """Request for UNINSTALL phase"""

    uninstall_data: UninstallData
    settings: Dict[str, Any] = field(factory=dict)


@frozen
class UninstallResponse:
    """Response for UNINSTALL phase"""

    uninstall_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


@frozen
class OauthCallbackRequest(AbstractRequest):
    """Request for OAUTH_CALLBACK phase"""

    o_auth_callback_data: OauthCallbackData


@frozen
class OauthCallbackResponse:
    """Response for OAUTH_CALLBACK phase"""

    o_auth_callback_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


@frozen
class EventRequest(AbstractRequest):
    """Request for EVENT phase"""

    event_data: EventData
    settings: Dict[str, Any] = field(factory=dict)


@frozen
class EventResponse:
    """Response for EVENT phase"""

    event_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


LifecycleRequest = Union[
    ConfigurationRequest,
    ConfirmationRequest,
    InstallRequest,
    UpdateRequest,
    UninstallRequest,
    OauthCallbackRequest,
    EventRequest,
]


REQUEST_BY_PHASE = {
    LifecyclePhase.CONFIGURATION: ConfigurationRequest,
    LifecyclePhase.CONFIRMATION: ConfirmationRequest,
    LifecyclePhase.INSTALL: InstallRequest,
    LifecyclePhase.UPDATE: UpdateRequest,
    LifecyclePhase.UNINSTALL: UninstallRequest,
    LifecyclePhase.OAUTH_CALLBACK: OauthCallbackRequest,
    LifecyclePhase.EVENT: EventRequest,
}

CONFIG_VALUE_BY_TYPE = {
    ConfigValueType.DEVICE: DeviceConfigValue,
    ConfigValueType.STRING: StringConfigValue,
}

CONFIG_SETTING_BY_TYPE = {
    ConfigSettingType.DEVICE: DeviceSetting,
    ConfigSettingType.TEXT: TextSetting,
    ConfigSettingType.BOOLEAN: BooleanSetting,
    ConfigSettingType.ENUM: EnumSetting,
    ConfigSettingType.LINK: LinkSetting,
    ConfigSettingType.PAGE: PageSetting,
    ConfigSettingType.IMAGE: ImageSetting,
    ConfigSettingType.ICON: IconSetting,
    ConfigSettingType.TIME: TimeSetting,
    ConfigSettingType.PARAGRAPH: ParagraphSetting,
    ConfigSettingType.EMAIL: EmailSetting,
    ConfigSettingType.DECIMAL: DecimalSetting,
    ConfigSettingType.NUMBER: NumberSetting,
    ConfigSettingType.PHONE: PhoneSetting,
    ConfigSettingType.OAUTH: OauthSetting,
}

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
    UNINSTALL = "UNINSTALL"
    OAUTH_CALLBACK = "OAUTH_CALLBACK"
    EVENT = "EVENT"


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


@frozen(kw_only=True)
class AbstractRequest(ABC):
    """Abstract parent class for all types of lifecycle requests."""

    lifecycle: LifecyclePhase
    execution_id: str
    locale: str
    version: str


@frozen(kw_only=True)
class AbstractSetting(ABC):
    """Abstract parent class for all types of config settings."""

    id: str
    name: str
    description: str
    required: Optional[bool] = False


@frozen(kw_only=True)
class DeviceSetting(AbstractSetting):
    """A DEVICE setting."""

    type: ConfigSettingType = ConfigSettingType.DEVICE
    multiple: bool
    capabilities: List[str]
    permissions: List[str]


@frozen(kw_only=True)
class TextSetting(AbstractSetting):
    """A TEXT setting."""

    type: ConfigSettingType = ConfigSettingType.TEXT
    default_value: str


@frozen(kw_only=True)
class BooleanSetting(AbstractSetting):
    """A BOOLEAN setting."""

    type: ConfigSettingType = ConfigSettingType.BOOLEAN
    default_value: BooleanValue


@frozen(kw_only=True)
class EnumOption:
    """An option within an ENUM setting"""

    id: str
    name: str


@frozen(kw_only=True)
class EnumOptionGroup:
    """A group of options within an ENUM setting"""

    name: str
    options: List[EnumOption]


@frozen(kw_only=True)
class EnumSetting(AbstractSetting):
    """An ENUM setting."""

    type: ConfigSettingType = ConfigSettingType.ENUM
    multiple: bool
    options: Optional[List[EnumOption]] = None
    grouped_options: Optional[List[EnumOptionGroup]] = None


@frozen(kw_only=True)
class LinkSetting(AbstractSetting):
    """A LINK setting."""

    type: ConfigSettingType = ConfigSettingType.LINK
    url: str
    image: str


@frozen(kw_only=True)
class PageSetting(AbstractSetting):
    """A PAGE setting."""

    type: ConfigSettingType = ConfigSettingType.PAGE
    page: str
    image: str


@frozen(kw_only=True)
class ImageSetting(AbstractSetting):
    """An IMAGE setting."""

    type: ConfigSettingType = ConfigSettingType.IMAGE
    image: str


@frozen(kw_only=True)
class IconSetting(AbstractSetting):
    """An ICON setting."""

    type: ConfigSettingType = ConfigSettingType.ICON
    image: str


@frozen(kw_only=True)
class TimeSetting(AbstractSetting):
    """A TIME setting."""

    type: ConfigSettingType = ConfigSettingType.TIME


@frozen(kw_only=True)
class ParagraphSetting(AbstractSetting):
    """A PARAGRAPH setting."""

    type: ConfigSettingType = ConfigSettingType.PARAGRAPH
    default_value: str


@frozen(kw_only=True)
class EmailSetting(AbstractSetting):
    """An EMAIL setting."""

    type: ConfigSettingType = ConfigSettingType.EMAIL


@frozen(kw_only=True)
class DecimalSetting(AbstractSetting):
    """A DECIMAL setting."""

    type: ConfigSettingType = ConfigSettingType.DECIMAL


@frozen(kw_only=True)
class NumberSetting(AbstractSetting):
    """A NUMBER setting."""

    type: ConfigSettingType = ConfigSettingType.NUMBER


@frozen(kw_only=True)
class PhoneSetting(AbstractSetting):
    """A PHONE setting."""

    type: ConfigSettingType = ConfigSettingType.PHONE


@frozen(kw_only=True)
class OauthSetting(AbstractSetting):
    """An OAUTH setting."""

    type: ConfigSettingType = ConfigSettingType.OAUTH
    browser: bool
    url_template: str


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


@frozen(kw_only=True)
class DeviceValue:
    device_id: str
    component_id: str


@frozen(kw_only=True)
class DeviceConfigValue:
    """DEVICE configuration value."""

    device_config: DeviceValue
    value_type: ConfigValueType = ConfigValueType.DEVICE


@frozen(kw_only=True)
class StringValue:
    value: str


@frozen(kw_only=True)
class StringConfigValue:
    """STRING configuration value."""

    string_config: StringValue
    value_type: ConfigValueType = ConfigValueType.STRING


ConfigValue = Union[
    DeviceConfigValue,
    StringConfigValue,
]


@frozen(kw_only=True)
class InstalledApp:
    """Installed application."""

    installed_app_id: str
    location_id: str
    config: Dict[str, List[ConfigValue]]
    permissions: List[str] = field(factory=list)


@frozen(kw_only=True)
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


@frozen(kw_only=True)
class DeviceHealthEvent:
    event_id: str
    location_id: str
    device_id: str
    hub_id: str
    status: str
    reason: str


@frozen(kw_only=True)
class HubHealthEvent:
    event_id: str
    location_id: str
    hub_id: str
    status: str
    reason: str


@frozen(kw_only=True)
class DeviceCommand:
    component_id: str
    capability: str
    command: str
    arguments: List[Any]  # TODO: exactly what do we get here?  Seems like this is too generic?


@frozen(kw_only=True)
class DeviceCommandsEvent:
    event_id: str
    device_id: str
    profile_id: str
    external_id: str
    commands: List[DeviceCommand]


@frozen(kw_only=True)
class ModeEvent:
    event_id: str
    location_id: str
    mode_id: str


@frozen(kw_only=True)
class TimerEvent:
    event_id: str
    name: str
    type: str
    time: DateTime
    expression: str


@frozen(kw_only=True)
class SecurityArmStateEvent:
    event_id: str
    location_id: str
    arm_state: str
    optional_arguments: Dict[str, Any]


@frozen(kw_only=True)
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


@frozen(kw_only=True)
class ConfirmationData:
    """Confirmation data."""

    app_id: str
    confirmation_url: str


@frozen(kw_only=True)
class ConfigInit:
    """Initialization data."""

    id: str
    name: str
    description: str
    permissions: List[str]
    first_page_id: str


@frozen(kw_only=True)
class ConfigRequestData:
    """Configuration data provided on the request."""

    installed_app_id: str
    phase: ConfigPhase
    page_id: str
    previous_page_id: str
    config: Dict[str, List[ConfigValue]]


@frozen(kw_only=True)
class ConfigInitData:
    """Configuration data provided in an INITIALIZATION response."""

    initialize: ConfigInit


@frozen(kw_only=True)
class ConfigSection:
    """A section within a configuration page."""

    name: str
    settings: List[ConfigSetting]


@frozen(kw_only=True)
class ConfigPage:
    """A page of configuration data for the CONFIGURATION phase."""

    page_id: str
    name: str
    previous_page_id: Optional[str]
    next_page_id: Optional[str]
    complete: bool
    sections: List[ConfigSection]


@frozen(kw_only=True)
class ConfigPageData:
    """Configuration data provided in an PAGE response."""

    page: ConfigPage


@frozen(kw_only=True)
class InstallData:
    """Install data."""

    auth_token: str
    refresh_token: str
    installed_app: InstalledApp


@frozen(kw_only=True)
class UpdateData:
    """Update data."""

    auth_token: str
    refresh_token: str
    installed_app: InstalledApp
    previous_config: Optional[Dict[str, List[ConfigValue]]] = None
    previous_permissions: List[str] = field(factory=list)


@frozen(kw_only=True)
class UninstallData:
    """Install data."""

    installed_app: InstalledApp


@frozen(kw_only=True)
class OauthCallbackData:
    installed_app_id: str
    url_path: str


@frozen(kw_only=True)
class EventData:
    """Event data."""

    auth_token: str
    installed_app: InstalledApp
    events: List[Event]


@frozen(kw_only=True)
class ConfirmationRequest(AbstractRequest):
    """Request for CONFIRMATION phase"""

    app_id: str
    confirmation_data: ConfirmationData
    settings: Dict[str, Any] = field(factory=dict)


@frozen(kw_only=True)
class ConfirmationResponse:
    """Response for CONFIRMATION phase"""

    target_url: str


@frozen(kw_only=True)
class ConfigurationRequest(AbstractRequest):
    """Request for CONFIGURATION phase"""

    configuration_data: ConfigRequestData
    settings: Dict[str, Any] = field(factory=dict)


@frozen(kw_only=True)
class ConfigurationInitResponse:
    """Response for CONFIGURATION/INITIALIZE phase"""

    configuration_data: ConfigInitData


@frozen(kw_only=True)
class ConfigurationPageResponse:
    """Response for CONFIGURATION/PAGE phase"""

    configuration_data: ConfigPageData


@frozen(kw_only=True)
class InstallRequest(AbstractRequest):
    """Request for INSTALL phase"""

    install_data: InstallData
    settings: Dict[str, Any] = field(factory=dict)


@frozen(kw_only=True)
class InstallResponse:
    """Response for INSTALL phase"""

    install_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


@frozen(kw_only=True)
class UpdateRequest(AbstractRequest):
    """Request for UPDATE phase"""

    update_data: UpdateData
    settings: Dict[str, Any] = field(factory=dict)


@frozen(kw_only=True)
class UpdateResponse:
    """Response for UPDATE phase"""

    update_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


@frozen(kw_only=True)
class UninstallRequest(AbstractRequest):
    """Request for UNINSTALL phase"""

    uninstall_data: UninstallData
    settings: Dict[str, Any] = field(factory=dict)


@frozen(kw_only=True)
class UninstallResponse:
    """Response for UNINSTALL phase"""

    uninstall_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


@frozen(kw_only=True)
class OauthCallbackRequest(AbstractRequest):
    """Request for OAUTH_CALLBACK phase"""

    o_auth_callback_data: OauthCallbackData


@frozen(kw_only=True)
class OauthCallbackResponse:
    """Response for OAUTH_CALLBACK phase"""

    o_auth_callback_data: Dict[str, Any] = field(factory=dict)  # always empty in the response


@frozen(kw_only=True)
class EventRequest(AbstractRequest):
    """Request for EVENT phase"""

    event_data: EventData
    settings: Dict[str, Any] = field(factory=dict)


@frozen(kw_only=True)
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

LifecycleResponse = Union[
    ConfigurationInitResponse,
    ConfigurationPageResponse,
    ConfirmationResponse,
    InstallResponse,
    UpdateResponse,
    UninstallResponse,
    OauthCallbackResponse,
    EventResponse,
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

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
SmartApp lifecycle.
"""

# See: https://developer-preview.smartthings.com/docs/connected-services/lifecycles/
#      https://developer-preview.smartthings.com/docs/connected-services/configuration/

from enum import Enum
from typing import Dict, Any, List, Optional

from humps.camel import case
from pydantic import BaseModel
from abc import ABC

from pydantic_yaml import YamlModel


class LifecyclePhase(Enum):
    CONFIRMATION = "CONFIRMATION"
    CONFIGURATION = "CONFIGURATION"
    INSTALL = "INSTALL"
    UPDATE = "UPDATE"
    EVENT = "EVENT"
    OAUTH_CALLBACK = "OAUTH_CALLBACK"
    UNINSTALL = "UNINSTALL"

class ConfigurationPhase(Enum):
    INITIALIZE = "INITIALIZE"
    PAGE = "PAGE"

class LifecycleModel(ABC, YamlModel):
    """Abstract lifecycle model"""
    class Config:
        """Turns snake-case attributes to camelcase in the interface."""
        # See: https://medium.com/analytics-vidhya/camel-case-models-with-fast-api-and-pydantic-5a8acb6c0eee
        alias_generator = lambda s: case(s)
        allow_population_by_field_name = True

class Setting(ABC, LifecycleModel):
    """Abstract parent class for all types of settings."""

class DeviceSetting(Setting):
    """A DEVICE setting."""

class TextSetting(Setting):
    """A TEXT setting."""

class BooleanSetting(Setting):
    """A BOOLEAN setting."""

class EnumSetting(Setting):
    """An ENUM setting."""

class LinkSetting(Setting):
    """A LINK setting."""

class PageSetting(Setting):
    """A PAGE setting."""

class ImageSetting(Setting):
    """An IMAGE setting."""

class IconSetting(Setting):
    """An ICON setting."""

class TimeSetting(Setting):
    """A TIME setting."""

class ParagraphSetting(Setting):
    """A PARAGRAPH setting."""

class EmailSetting(Setting):
    """An EMAIL setting."""

class DecimalSetting(Setting):
    """A DECIMAL setting."""

class NumberSetting(Setting):
    """A NUMBER setting."""

class PhoneSetting(Setting):
    """A PHONE setting."""

class OauthSetting(Setting):
    """An OAUTH setting."""

class ConfirmData(LifecycleModel):
    """Data for the CONFIRMATION phase."""
    app_id: str
    confirmation_url: str

class ConfigData(LifecycleModel):
   """Configuration data."""
   installed_app_id: str
   phase: ConfigurationPhase
   page_id: str
   previous_page_id: str
   config: Dict[str, Any]

class InstalledApp(LifecycleModel):
    """Installed application"""
    installed_app_id: str
    location_id: str
    config: Dict[str, Any]
    previousConfig: Optional[Dict[str, Any]]
    permissions: List[str]

class InstallData(LifecycleModel):
   """Install data."""
   auth_token: str
   refresh_token: str
   installed_app: InstalledApp

class UpdateData(LifecycleModel):
   """Install data."""
   auth_token: str
   refresh_token: str
   installed_app: InstalledApp

# TODO: I can't find any specific documentation for events, except the source code for the Javascript client
#       https://github.com/SmartThingsCommunity/smartapp-sdk-nodejs/blob/f1ef97ec9c6dc270ba744197b842c6632c778987/lib/lifecycle-events.d.ts
#       At least it hasn't been changed in over a year, so it's kinda (?) stable?
class EventData(LifecycleModel):
    """Event data."""
    auth_token: str
    installed_app: InstalledApp
    events: List[Event]

class ConfigInit(LifecycleModel):
    """Initialization data for the CONFIGURATION phase."""
    name: str
    description: str
    id: str
    permissions: List[str]
    first_page_id: str

class ConfigSection(LifecycleModel):
    """A section within a configuration page."""
    name: str
    settings: List[Setting]

class ConfigPage(LifecycleModel):
    """A page of configuration data for the CONFIGURATION phase."""
    page_id: str
    name: str
    next_page_id: str
    previous_page_id: str
    complete: bool = False
    sections: List[ConfigSection]

class ConfirmationRequest(LifecycleModel):
    """Request for CONFIRMATION phase"""
    lifecycle: LifecyclePhase = LifecyclePhase.CONFIRMATION
    execution_id: str
    app_id: str
    locale: str = "en" # we only support English for now
    version: str
    confirmation_data: ConfirmData
    settings: Dict[str, Any]

class ConfirmationResponse(LifecycleModel):
    """Response for CONFIRMATION phase"""
    target_url: str

class ConfigurationRequest(LifecycleModel):
    """Request for CONFIGURATION phase"""
    lifecycle: LifecyclePhase = LifecyclePhase.CONFIGURATION
    execution_id: str
    locale: str = "en" # we only support English for now
    version: str
    configuration_data: ConfigData
    settings: Dict[str, Any]

class ConfigurationResponse(LifecycleModel):
    """Response for CONFIGURATION phase"""
    initialize: Optional[ConfigInit]
    page: Optional[ConfigPage]

class InstallRequest(LifecycleModel):
    """Request for INSTALL phase"""
    lifecycle: LifecyclePhase = LifecyclePhase.INSTALL
    execution_id: str
    locale: str = "en"  # we only support English for now
    version: str
    install_data: InstallData
    settings: Dict[str, Any]

class InstallResponse(LifecycleModel):
    """Response for INSTALL phase"""
    install_data: Dict[str, Any] = {}  # always empty in the response

class UpdateRequest(LifecycleModel):
    """Request for UPDATE phase"""
    lifecycle: LifecyclePhase = LifecyclePhase.UPDATE
    execution_id: str
    locale: str = "en"  # we only support English for now
    version: str
    update_data: UpdateData
    settings: Dict[str, Any]

class UpdateResponse(LifecycleModel):
    """Response for UPDATE phase"""
    update_data: Dict[str, Any] = {}  # always empty in the response

class EventRequest(LifecycleModel):
    """Request for EVENT phase"""
    lifecycle: LifecyclePhase = LifecyclePhase.EVENT
    execution_id: str
    locale: str = "en"  # we only support English for now
    version: str
    event_data: EventData
    settings: Dict[str, Any]

class EventResponse(LifecycleModel):
    """Response for EVENT phase"""
    event_data: Dict[str, Any] = {}  # always empty in the response

class OauthCallbackRequest(LifecycleModel):
    """Request for OAUTH_CALLBACK phase"""
    lifecycle: LifecyclePhase = LifecyclePhase.OAUTH_CALLBACK

class OauthCallbackResponse(LifecycleModel):
    """Response for OAUTH_CALLBACK phase"""

class UninstallRequest(LifecycleModel):
    """Request for UNINSTALL phase"""
    lifecycle: LifecyclePhase = LifecyclePhase.UNINSTALL

class UninstallResponse(LifecycleModel):
    """Response for UNINSTALL phase"""
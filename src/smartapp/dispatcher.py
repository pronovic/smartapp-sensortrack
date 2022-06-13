# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Manage the requests and responses that are part of the SmartApp lifecycle.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

from attr import frozen

from .converter import CONVERTER
from .interface import (
    ConfigInit,
    ConfigInitData,
    ConfigPage,
    ConfigPageData,
    ConfigPhase,
    ConfigSection,
    ConfigurationInitResponse,
    ConfigurationPageResponse,
    ConfigurationRequest,
    ConfirmationRequest,
    ConfirmationResponse,
    EventRequest,
    EventResponse,
    InstallRequest,
    InstallResponse,
    LifecycleRequest,
    LifecycleResponse,
    OauthCallbackRequest,
    OauthCallbackResponse,
    UninstallRequest,
    UninstallResponse,
    UpdateRequest,
    UpdateResponse,
)


class SmartAppEventHandler(ABC):
    """
    Application event handler for SmartApp lifecycle events.

    Inherit from this class to implement your own application-specific event handler.  In
    most cases, your implementation can be empty.  See notes below.

    - CONFIRMATION: normally no callback needed, since the dispatcher logs the app id and confirmation URL
    - CONFIGURATION: normally no callback needed, since the dispatcher has the information it needs to respond
    - INSTALL/UPDATE: set up or replace subscriptions and schedules and persist required data, if any
    - UNINSTALL: remove persisted data, if any
    - OAUTH_CALLBACK: coordinate with your oauth provider as needed
    - EVENT: handle SmartThings events or scheduled triggers

    The EventRequest object that you receive for the EVENT callback includes an
    authorization token and also the entire configuration bundle for the installed
    application.  So, if your SmartApp is built around event handling and scheduled
    actions triggered by SmartThings, your handler can probably be stateless.  There is
    probably is not any need to persist any of the data returned in the INSTALL or UPDATE
    lifecycle events into your own data store.

    Note that SmartAppHandler is a synchronous and single-threaded interface.  The
    assumption is that if you need high-volume asynchronous or multi-threaded processing,
    you will implement that at the tier above this where the actual POST requests are
    accepted from remote callers.
    """

    @abstractmethod
    def handle_confirmation(self, request: ConfirmationRequest) -> None:
        """Handle a CONFIRMATION lifecycle request"""

    @abstractmethod
    def handle_configuration(self, request: ConfigurationRequest) -> None:
        """Handle a CONFIGURATION lifecycle request."""

    @abstractmethod
    def handle_install(self, request: InstallRequest) -> None:
        """Handle an INSTALL lifecycle request."""

    @abstractmethod
    def handle_update(self, request: UpdateRequest) -> None:
        """Handle an UPDATE lifecycle request."""

    @abstractmethod
    def handle_uninstall(self, request: UninstallRequest) -> None:
        """Handle an UNINSTALL lifecycle request."""

    @abstractmethod
    def handle_oauth_callback(self, request: OauthCallbackRequest) -> None:
        """Handle an OAUTH_CALLBACK lifecycle request."""

    @abstractmethod
    def handle_event(self, request: EventRequest) -> None:
        """Handle an EVENT lifecycle request."""


@frozen(kw_only=True)
class SmartAppConfigPage:
    """
    A page of configuration for the SmartApp.
    """

    page_name: str
    sections: List[ConfigSection]


@frozen(kw_only=True)
class SmartAppDefinition:

    # noinspection PyUnresolvedReferences
    """
    The definition of the SmartApp.

    All of this data would normally be static for any given version of your application.
    If you wish, you can maintain the definition in YAML or JSON in your source tree
    and parse it with `smartapp.converter.CONVERTER`.

    Keep in mind that the JSON or YAML format on disk will be consistent with the SmartThings
    lifecycle API, so it will use camel case attribute names (like `configPages`) rather than
    the Python attribute names you see in source code (like `config_pages`).

    Attributes:
        id(str): Identifier for this SmartApp
        name(str): Name of the SmartApp
        description(str): Description of the SmartApp
        permissions(List[str]): Permissions that the SmartApp requires
        config_pages(List[SmartAppConfigPage]): Configuration pages that the SmartApp will offer users
    """
    id: str
    name: str
    description: str
    target_url: str
    permissions: List[str]
    config_pages: List[SmartAppConfigPage]


@frozen(kw_only=True)
class SmartAppDispatcher:

    # noinspection PyUnresolvedReferences
    """
    Dispatcher to manage the requests and responses that are part of the SmartApp lifecycle.

    You must provide both a definition and an event handler, but you do not necessarily need
    to implement a handler method for every lifecycle event.  For more information, see
    `SmartAppHandler`.

    Attributes:
        definition(SmartAppDefinition): The static definition for the SmartApp
        event_handler(SmartAppEventHandler): Application event handler for SmartApp lifecycle events
    """

    definition: SmartAppDefinition
    event_handler: SmartAppEventHandler

    def dispatch(self, request_json: str) -> Tuple[int, str]:
        """
        Dispatch a request, responding to SmartThings and invoking callbacks as needed.

        Args:
            request_json(str): Request JSON payload received from the POST

        Returns:
            (int, str): HTTP status code and response JSON payload that to be returned to the POST caller
        """
        try:
            # TODO: check signature and return 401 if it's not valid (but this is a relatively large effort)
            request: LifecycleRequest = CONVERTER.from_json(request_json, LifecycleRequest)  # type: ignore
            response = self._handle_request(request)
            return 200, CONVERTER.to_json(response)
        except Exception:  # pylint: disable=broad-except:
            # TODO: should have some logging in here
            return 500, ""  # at this point, any exception is a server error

    def _handle_request(self, request: LifecycleRequest) -> LifecycleResponse:
        """Handle a lifecycle request, returning the appropriate response."""
        if isinstance(request, ConfirmationRequest):
            # TODO: if we log this, then the caller doesn't need to implement the event handler
            self.event_handler.handle_confirmation(request)
            return ConfirmationResponse(target_url=self.definition.target_url)
        elif isinstance(request, ConfigurationRequest):
            response = self._handle_config_request(request)
            self.event_handler.handle_configuration(request)
            return response
        elif isinstance(request, InstallRequest):
            self.event_handler.handle_install(request)
            return InstallResponse()
        elif isinstance(request, UpdateRequest):
            self.event_handler.handle_update(request)
            return UpdateResponse()
        elif isinstance(request, UninstallRequest):
            self.event_handler.handle_uninstall(request)
            return UninstallResponse()
        elif isinstance(request, OauthCallbackRequest):
            self.event_handler.handle_oauth_callback(request)
            return OauthCallbackResponse()
        elif isinstance(request, EventRequest):
            self.event_handler.handle_event(request)
            return EventResponse()
        else:
            raise ValueError("Unknown lifecycle event")

    def _handle_config_request(self, request: ConfigurationRequest) -> Union[ConfigurationInitResponse, ConfigurationPageResponse]:
        """Handle a CONFIGURATION lifecycle request, returning an appropriate response."""
        if request.configuration_data.phase == ConfigPhase.INITIALIZE:
            return ConfigurationInitResponse(
                configuration_data=ConfigInitData(
                    initialize=ConfigInit(
                        id=self.definition.id,
                        name=self.definition.name,
                        description=self.definition.description,
                        permissions=self.definition.permissions,
                        first_page_id="1",
                    )
                )
            )
        else:  # if request.configuration_data.phase == ConfigPhase.PAGE:
            page_id = int(request.configuration_data.page_id)
            previous_page_id = None if page_id == 1 else str(page_id - 1)
            next_page_id = None if page_id >= len(self.definition.config_pages) else str(page_id + 1)
            complete = page_id >= len(self.definition.config_pages)
            pages = self.definition.config_pages[page_id - 1]  # page_id is 1-based
            return ConfigurationPageResponse(
                configuration_data=ConfigPageData(
                    page=ConfigPage(
                        name=pages.page_name,
                        page_id=request.configuration_data.page_id,
                        previous_page_id=previous_page_id,
                        next_page_id=next_page_id,
                        complete=complete,
                        sections=pages.sections,
                    )
                )
            )

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Manage the requests and responses that are part of the SmartApp lifecycle.
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Mapping, Optional, Tuple, Union

from attr import frozen

from .converter import CONVERTER
from .interface import (
    AbstractRequest,
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

    Inherit from this class to implement your own application-specific event handler.
    The application-specific event handler is always called first, before any default
    event handler logic in the dispatcher itself.

    The correlation id is an optional value that you can associate with your log messages.
    It may aid in debugging if you need to contact SmartThings for support.

    Some lifecycle events do not require you to implement any custom event handler logic:

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
    def handle_confirmation(self, correlation_id: Optional[str], request: ConfirmationRequest) -> None:
        """Handle a CONFIRMATION lifecycle request"""

    @abstractmethod
    def handle_configuration(self, correlation_id: Optional[str], request: ConfigurationRequest) -> None:
        """Handle a CONFIGURATION lifecycle request."""

    @abstractmethod
    def handle_install(self, correlation_id: Optional[str], request: InstallRequest) -> None:
        """Handle an INSTALL lifecycle request."""

    @abstractmethod
    def handle_update(self, correlation_id: Optional[str], request: UpdateRequest) -> None:
        """Handle an UPDATE lifecycle request."""

    @abstractmethod
    def handle_uninstall(self, correlation_id: Optional[str], request: UninstallRequest) -> None:
        """Handle an UNINSTALL lifecycle request."""

    @abstractmethod
    def handle_oauth_callback(self, correlation_id: Optional[str], request: OauthCallbackRequest) -> None:
        """Handle an OAUTH_CALLBACK lifecycle request."""

    @abstractmethod
    def handle_event(self, correlation_id: Optional[str], request: EventRequest) -> None:
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
class SmartAppRequestContext:

    # noinspection PyUnresolvedReferences
    """
    SmartApp request context.

    Attributes:
        headers(Mapping[str, str]): The request headers, assumed to be accessible in case-insenstive fashion
        request_json(str): The request JSON from the POST body
    """

    headers: Mapping[str, str]
    request_json: str

    def header(self, header: str) -> Optional[str]:
        """Return a named header or None if it does not exist."""
        return self.headers[header] if header in self.headers else None

    @property
    def authorization(self) -> Optional[str]:
        return self.header("authorization")

    @property
    def correlation_id(self) -> Optional[str]:
        return self.header("x-st-correlation")


@frozen(kw_only=True)
class SmartAppDispatcher:

    # noinspection PyUnresolvedReferences
    """
    Dispatcher to manage the requests and responses that are part of the SmartApp lifecycle.

    You must provide both a definition and an event handler, but in some cases the handler
    methods will probably be no-ops without any custom logic.  For more information, see
    `SmartAppEventHandler`.

    Attributes:
        definition(SmartAppDefinition): The static definition for the SmartApp
        event_handler(SmartAppEventHandler): Application event handler for SmartApp lifecycle events
    """

    definition: SmartAppDefinition
    event_handler: SmartAppEventHandler

    def dispatch(self, context: SmartAppRequestContext) -> Tuple[int, str]:
        """
        Dispatch a request, responding to SmartThings and invoking callbacks as needed.

        Args:
            context(SmartAppRequestContet): Request context, including headers and JSON body

        Returns:
            (int, str): HTTP status code and response JSON payload that to be returned to the POST caller
        """
        try:
            # TODO: check signature and return 401 if it's not valid (but this is a relatively large effort)
            request: LifecycleRequest = CONVERTER.from_json(context.request_json, LifecycleRequest)  # type: ignore
            response = self._handle_request(context.correlation_id, request)
            return 200, CONVERTER.to_json(response)
        except Exception:  # pylint: disable=broad-except:
            logging.exception("[%s] Error handling lifecycle request, returning 500 response", context.correlation_id)
            return 500, ""

    def _handle_request(self, correlation_id: Optional[str], request: AbstractRequest) -> LifecycleResponse:
        """Handle a lifecycle request, returning the appropriate response."""
        logging.info("[%s] Handling %s request executionId=%s", correlation_id, request.lifecycle, request.execution_id)
        logging.debug("[%s] Request: %s", correlation_id, request)  # this is safe because secrets are not shown
        if isinstance(request, ConfirmationRequest):
            self.event_handler.handle_confirmation(correlation_id, request)
            return self._handle_confirmation_request(correlation_id, request)
        elif isinstance(request, ConfigurationRequest):
            self.event_handler.handle_configuration(correlation_id, request)
            return self._handle_config_request(request)
        elif isinstance(request, InstallRequest):
            self.event_handler.handle_install(correlation_id, request)
            return InstallResponse()
        elif isinstance(request, UpdateRequest):
            self.event_handler.handle_update(correlation_id, request)
            return UpdateResponse()
        elif isinstance(request, UninstallRequest):
            self.event_handler.handle_uninstall(correlation_id, request)
            return UninstallResponse()
        elif isinstance(request, OauthCallbackRequest):
            self.event_handler.handle_oauth_callback(correlation_id, request)
            return OauthCallbackResponse()
        elif isinstance(request, EventRequest):
            self.event_handler.handle_event(correlation_id, request)
            return EventResponse()
        else:
            raise ValueError("Unknown lifecycle event")

    def _handle_confirmation_request(self, correlation_id: Optional[str], request: ConfirmationRequest) -> ConfirmationResponse:
        """Handle a CONFIRMATION lifecycle request, logging data and returning an appropriate response."""
        logging.info("[%s] CONFIRMATION [%s]: [%s]", correlation_id, request.app_id, request.confirmation_data.confirmation_url)
        return ConfirmationResponse(target_url=self.definition.target_url)

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

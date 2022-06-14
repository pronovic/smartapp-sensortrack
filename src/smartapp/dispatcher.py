# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Manage the requests and responses that are part of the SmartApp lifecycle.
"""
import logging
from typing import Mapping, Optional, Union

from attr import field, frozen

from .converter import CONVERTER
from .interface import (
    AbstractRequest,
    BadRequestError,
    ConfigInit,
    ConfigInitData,
    ConfigPage,
    ConfigPageData,
    ConfigPhase,
    ConfigurationInitResponse,
    ConfigurationPageResponse,
    ConfigurationRequest,
    ConfirmationRequest,
    ConfirmationResponse,
    EventRequest,
    EventResponse,
    InstallRequest,
    InstallResponse,
    InternalError,
    LifecycleRequest,
    LifecycleResponse,
    OauthCallbackRequest,
    OauthCallbackResponse,
    SmartAppDefinition,
    SmartAppDispatcherConfig,
    SmartAppError,
    SmartAppEventHandler,
    UninstallRequest,
    UninstallResponse,
    UpdateRequest,
    UpdateResponse,
)
from .signature import check_signature

CORRELATION_ID = "x-st-correlation"


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
    config: SmartAppDispatcherConfig = field(factory=SmartAppDispatcherConfig)

    def dispatch(self, headers: Mapping[str, str], request_json: str) -> str:
        """
        Dispatch a request, responding to SmartThings and invoking callbacks as needed.

        Args:
            headers(Mapping[str, str]): The request headers, assumed to be accessible in case-insenstive fashion
            request_json(str): The request JSON from the POST body

        Returns:
            str: Response JSON payload that to be returned to the POST caller

        Raises:
            SmartAppError: If processing fails
        """
        correlation_id = headers[CORRELATION_ID] if CORRELATION_ID in headers else None
        try:
            if self.config.check_signatures:
                check_signature(correlation_id, headers, request_json, self.config.clock_skew_sec)
            request: LifecycleRequest = CONVERTER.from_json(request_json, LifecycleRequest)  # type: ignore
            response = self._handle_request(correlation_id, request)
            return CONVERTER.to_json(response)
        except SmartAppError as e:
            raise e
        except ValueError as e:
            raise BadRequestError("%s" % e, correlation_id) from e
        except Exception as e:  # pylint: disable=broad-except:
            raise InternalError("%s" % e, correlation_id) from e

    def _handle_request(self, correlation_id: Optional[str], request: AbstractRequest) -> LifecycleResponse:
        """Handle a lifecycle request, returning the appropriate response."""
        logging.info("[%s] Handling %s request executionId=%s", correlation_id, request.lifecycle, request.execution_id)
        logging.debug("[%s] Request: %s", correlation_id, request)  # this is safe because secrets are not shown
        if isinstance(request, ConfirmationRequest):
            self.event_handler.handle_confirmation(correlation_id, request)
            return self._handle_confirmation_request(request)
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

    def _handle_confirmation_request(self, request: ConfirmationRequest) -> ConfirmationResponse:
        """Handle a CONFIRMATION lifecycle request, logging data and returning an appropriate response."""
        logging.info("CONFIRMATION [%s]: [%s]", request.app_id, request.confirmation_data.confirmation_url)
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

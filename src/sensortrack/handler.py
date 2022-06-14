# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
SmartApp event handler.
"""
from typing import Optional

from smartapp.interface import (
    ConfigurationRequest,
    ConfirmationRequest,
    EventRequest,
    InstallRequest,
    OauthCallbackRequest,
    SmartAppEventHandler,
    UninstallRequest,
    UpdateRequest,
)


class EventHandler(SmartAppEventHandler):

    """SmartApp event handler."""

    def handle_confirmation(self, correlation_id: Optional[str], request: ConfirmationRequest) -> None:
        pass

    def handle_configuration(self, correlation_id: Optional[str], request: ConfigurationRequest) -> None:
        pass

    def handle_install(self, correlation_id: Optional[str], request: InstallRequest) -> None:
        pass

    def handle_update(self, correlation_id: Optional[str], request: UpdateRequest) -> None:
        pass

    def handle_uninstall(self, correlation_id: Optional[str], request: UninstallRequest) -> None:
        pass

    def handle_oauth_callback(self, correlation_id: Optional[str], request: OauthCallbackRequest) -> None:
        pass

    def handle_event(self, correlation_id: Optional[str], request: EventRequest) -> None:
        pass

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
SmartApp event handler.
"""
from smartapp.dispatcher import SmartAppEventHandler
from smartapp.interface import (
    ConfigurationRequest,
    ConfirmationRequest,
    EventRequest,
    InstallRequest,
    OauthCallbackRequest,
    UninstallRequest,
    UpdateRequest,
)


class EventHandler(SmartAppEventHandler):

    """SmartApp event handler."""

    def handle_confirmation(self, request: ConfirmationRequest) -> None:
        pass

    def handle_configuration(self, request: ConfigurationRequest) -> None:
        pass

    def handle_install(self, request: InstallRequest) -> None:
        pass

    def handle_update(self, request: UpdateRequest) -> None:
        pass

    def handle_uninstall(self, request: UninstallRequest) -> None:
        pass

    def handle_oauth_callback(self, request: OauthCallbackRequest) -> None:
        pass

    def handle_event(self, request: EventRequest) -> None:
        pass

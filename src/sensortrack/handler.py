# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unnecessary-pass:

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
        """Handle a CONFIRMATION lifecycle request"""
        pass  # no action needed for this event, the standard dispatcher does everything that's needed

    def handle_configuration(self, correlation_id: Optional[str], request: ConfigurationRequest) -> None:
        """Handle a CONFIGURATION lifecycle request."""
        pass  # no action needed for this event, the standard dispatcher does everything that's needed

    def handle_uninstall(self, correlation_id: Optional[str], request: UninstallRequest) -> None:
        """Handle an UNINSTALL lifecycle request."""
        pass  # no action needed for this event, subscriptions and schedules have already been deleted

    def handle_oauth_callback(self, correlation_id: Optional[str], request: OauthCallbackRequest) -> None:
        """Handle an OAUTH_CALLBACK lifecycle request."""
        pass  # no action needed for this event, we don't use any special oauth integration

    def handle_install(self, correlation_id: Optional[str], request: InstallRequest) -> None:
        """Handle an INSTALL lifecycle request."""
        pass  # TODO: subscribe to state change events for configured devices

    def handle_update(self, correlation_id: Optional[str], request: UpdateRequest) -> None:
        """Handle an UPDATE lifecycle request."""
        pass  # TODO: delete and replace existing subscriptions for configured devices

    def handle_event(self, correlation_id: Optional[str], request: EventRequest) -> None:
        """Handle an EVENT lifecycle request."""
        pass  # TODO: handle events where we get data when sensors change state (not sure exactly how this works)

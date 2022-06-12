# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
OAUTH_CALLBACK phase in the SmartApp lifecycle.
"""
from typing import Any, Dict

from attrs import frozen

from sensortrack.lifecycle.interface.lifecycle import AbstractRequest, LifecyclePhase

PHASE = LifecyclePhase.OAUTH_CALLBACK


@frozen
class CallbackData:
    installed_app_id: str
    url_path: str


# TODO: figure out how to special-case "oauth_callback_data" to "oAuthCallbackData", ugh
#       might work with o_auth_callback_data, though ugly


@frozen
class OauthCallbackRequest(AbstractRequest):
    """Request for OAUTH_CALLBACK phase"""

    o_auth_callback_data: CallbackData


@frozen
class OauthCallbackResponse:
    """Response for OAUTH_CALLBACK phase"""

    o_auth_callback_data: Dict[str, Any] = {}  # always empty in the response

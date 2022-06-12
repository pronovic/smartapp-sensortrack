# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
CONFIRMATION phase in the SmartApp lifecycle.
"""
from typing import Any, Dict

from attrs import frozen

from sensortrack.lifecycle.interface.lifecycle import AbstractRequest, LifecyclePhase

PHASE = LifecyclePhase.CONFIRMATION


@frozen
class ConfirmationData:
    """Confirmation data."""

    app_id: str
    confirmation_url: str


@frozen
class ConfirmationRequest(AbstractRequest):
    """Request for CONFIRMATION phase"""

    app_id: str
    confirmation_data: ConfirmationData
    settings: Dict[str, Any]


@frozen
class ConfirmationResponse:
    """Response for CONFIRMATION phase"""

    target_url: str

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
UPDATE phase in the SmartApp lifecycle.
"""
from typing import Any, Dict

from attrs import frozen

from sensortrack.lifecycle.interface.installedapp import InstalledApp
from sensortrack.lifecycle.interface.lifecycle import AbstractRequest, LifecyclePhase

PHASE = LifecyclePhase.UPDATE


@frozen
class UpdateData:
    """Update data."""

    auth_token: str
    refresh_token: str
    installed_app: InstalledApp


@frozen
class UpdateRequest(AbstractRequest):
    """Request for UPDATE phase"""

    update_data: UpdateData
    settings: Dict[str, Any]


@frozen
class UpdateResponse:
    """Response for UPDATE phase"""

    update_data: Dict[str, Any] = {}  # always empty in the response

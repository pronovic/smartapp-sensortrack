# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
UPDATE phase in the SmartApp lifecycle.
"""
from typing import Any, Dict

from attrs import frozen

from sensortrack.lifecycle.common import LifecyclePhase, LifecycleRequest
from sensortrack.lifecycle.installedapp import InstalledApp

PHASE = LifecyclePhase.UPDATE


@frozen
class UpdateData:
    """Update data."""

    auth_token: str
    refresh_token: str
    installed_app: InstalledApp


@frozen
class UpdateRequest(LifecycleRequest):
    """Request for UPDATE phase"""

    update_data: UpdateData
    settings: Dict[str, Any]


@frozen
class UpdateResponse:
    """Response for UPDATE phase"""

    update_data: Dict[str, Any] = {}  # always empty in the response

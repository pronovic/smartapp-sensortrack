# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
INSTALL phase in the SmartApp lifecycle.
"""
from typing import Any, Dict

from attrs import frozen

from sensortrack.lifecycle.interface.installedapp import InstalledApp
from sensortrack.lifecycle.interface.lifecycle import AbstractRequest, LifecyclePhase

PHASE = LifecyclePhase.INSTALL


@frozen
class InstallData:
    """Install data."""

    auth_token: str
    refresh_token: str
    installed_app: InstalledApp


@frozen
class InstallRequest(AbstractRequest):
    """Request for INSTALL phase"""

    install_data: InstallData
    settings: Dict[str, Any]


@frozen
class InstallResponse:
    """Response for INSTALL phase"""

    install_data: Dict[str, Any] = {}  # always empty in the response

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
UNINSTALL phase in the SmartApp lifecycle.
"""
from typing import Any, Dict

from attrs import frozen

from sensortrack.lifecycle.common import LifecyclePhase, LifecycleRequest
from sensortrack.lifecycle.installedapp import InstalledApp

PHASE = LifecyclePhase.UNINSTALL


@frozen
class UninstallData:
    """Install data."""

    installed_app: InstalledApp


@frozen
class UninstallRequest(LifecycleRequest):
    """Request for UNINSTALL phase"""

    update_data: UninstallData
    settings: Dict[str, Any]


@frozen
class UninstallResponse:
    """Response for UNINSTALL phase"""

    uninstall_data: Dict[str, Any] = {}  # always empty in the response

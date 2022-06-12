# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
UNINSTALL phase in the SmartApp lifecycle.
"""
from typing import Any, Dict

from attrs import frozen

from sensortrack.lifecycle.interface.installedapp import InstalledApp
from sensortrack.lifecycle.interface.lifecycle import AbstractRequest, LifecyclePhase

PHASE = LifecyclePhase.UNINSTALL


@frozen
class UninstallData:
    """Install data."""

    installed_app: InstalledApp


@frozen
class UninstallRequest(AbstractRequest):
    """Request for UNINSTALL phase"""

    uninstall_data: UninstallData
    settings: Dict[str, Any]


@frozen
class UninstallResponse:
    """Response for UNINSTALL phase"""

    uninstall_data: Dict[str, Any] = {}  # always empty in the response

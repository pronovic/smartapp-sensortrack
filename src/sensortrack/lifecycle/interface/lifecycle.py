# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
High-level lifecycle definitions.
"""

# See: https://developer-preview.smartthings.com/docs/connected-services/lifecycles/
#      https://developer-preview.smartthings.com/docs/connected-services/configuration/

from abc import ABC
from enum import Enum

from attrs import frozen


class LifecyclePhase(Enum):
    CONFIRMATION = "CONFIRMATION"
    CONFIGURATION = "CONFIGURATION"
    INSTALL = "INSTALL"
    UPDATE = "UPDATE"
    EVENT = "EVENT"
    OAUTH_CALLBACK = "OAUTH_CALLBACK"
    UNINSTALL = "UNINSTALL"


@frozen
class AbstractRequest(ABC):
    """Abstract parent class for all types of lifecycle requests."""

    lifecycle: LifecyclePhase
    execution_id: str
    locale: str
    version: str

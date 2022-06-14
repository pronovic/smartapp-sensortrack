# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Verify HTTP signatures on SmartApp lifecycle event requests.
"""

from smartapp.interface import SmartAppDefinition, SmartAppDispatcherConfig, SmartAppRequestContext


# pylint: disable=unused-argument:
def check_signature(context: SmartAppRequestContext, config: SmartAppDispatcherConfig, definition: SmartAppDefinition) -> None:

    """Verify HTTP signatures on a SmartApp request, raising SignatureError if invalid."""

    # TODO: implement check_signature()

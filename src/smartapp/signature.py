# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Verify HTTP signatures on SmartApp lifecycle event requests.
"""
from typing import Mapping, Optional


# pylint: disable=unused-argument:
def check_signature(correlation_id: Optional[str], headers: Mapping[str, str], request_json: str, clock_skew_sec: int) -> None:

    """Verify HTTP signatures on a SmartApp request, raising SignatureError if invalid."""

    # TODO: implement check_signature()

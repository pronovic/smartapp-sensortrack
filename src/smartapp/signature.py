# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Verify HTTP signatures on SmartApp lifecycle event requests.
"""
from typing import Mapping


def check_signature(headers: Mapping[str, str], request_json: str, clock_skew_sec: int) -> None:  # pylint: disable=unused-argument:

    """Verify HTTP signatures on a SmartApp request, raising SignatureError if invalid."""

    # TODO: implement check_signature()

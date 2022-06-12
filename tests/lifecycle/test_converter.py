# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name:

import os

import pytest

from sensortrack.lifecycle.converter import CONVERTER
from sensortrack.lifecycle.interface import (
    ConfigRequest,
    ConfirmationRequest,
    EventRequest,
    InstallRequest,
    LifecycleRequest,
    OauthCallbackRequest,
    UninstallRequest,
    UpdateRequest,
    LifecyclePhase,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_converter")
REQUEST_DIR = os.path.join(FIXTURE_DIR, "request")


@pytest.fixture
def requests():
    data = {}
    for f in os.listdir(REQUEST_DIR):
        p = os.path.join(REQUEST_DIR, f)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as r:
                data[f] = r.read()
    return data


class TestParseJsonRoundTrip:

    # This spot-checks that we get the right type from each example file and that we can round-trip it succesfully
    # Other tests below confirm that we are actually parsing each file properly

    @pytest.mark.parametrize(
        "source,expected",
        [
            ("CONFIRMATION", ConfirmationRequest),
            ("CONFIGURATION", ConfigRequest),
            ("INSTALL", InstallRequest),
            ("UPDATE", UpdateRequest),
            ("UNINSTALL", UninstallRequest),
            ("OAUTH_CALLBACK", OauthCallbackRequest),
            ("EVENT-DEVICE", EventRequest),
            ("EVENT-TIMER", EventRequest),
        ],
    )
    def test_round_trip(self, source, expected, requests):
        j = requests["%s.json" % source]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, expected)
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

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


class TestParseJsonRequest:
    def test_confirmation(self, requests):
        j = requests["CONFIRMATION.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, ConfirmationRequest)

    def test_configuration(self, requests):
        j = requests["CONFIGURATION.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, ConfigRequest)

    def test_install(self, requests):
        j = requests["INSTALL.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, InstallRequest)

    def test_update(self, requests):
        j = requests["UPDATE.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, UpdateRequest)

    def test_event_device(self, requests):
        j = requests["EVENT-DEVICE.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, EventRequest)

    def test_event_timer(self, requests):
        j = requests["EVENT-TIMER.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, EventRequest)

    def test_oauth_callback(self, requests):
        j = requests["OAUTH_CALLBACK.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, OauthCallbackRequest)

    def test_uninstall(self, requests):
        j = requests["UNINSTALL.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, UninstallRequest)

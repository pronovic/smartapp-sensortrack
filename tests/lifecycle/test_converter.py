# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,invalid-name:

import os
from typing import Dict

import pendulum
import pytest

from sensortrack.lifecycle.converter import CONVERTER
from sensortrack.lifecycle.interface import (
    ConfigInit,
    ConfigInitData,
    ConfigPage,
    ConfigPageData,
    ConfigPhase,
    ConfigRequestData,
    ConfigSection,
    ConfigurationInitResponse,
    ConfigurationPageResponse,
    ConfigurationRequest,
    ConfirmationData,
    ConfirmationRequest,
    ConfirmationResponse,
    DeviceConfigValue,
    DeviceEvent,
    DeviceSetting,
    DeviceValue,
    Event,
    EventData,
    EventRequest,
    EventResponse,
    EventType,
    InstallData,
    InstalledApp,
    InstallRequest,
    InstallResponse,
    LifecyclePhase,
    LifecycleRequest,
    OauthCallbackData,
    OauthCallbackRequest,
    OauthCallbackResponse,
    StringConfigValue,
    StringValue,
    TimerEvent,
    UninstallData,
    UninstallRequest,
    UninstallResponse,
    UpdateData,
    UpdateRequest,
    UpdateResponse,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_converter")
REQUEST_DIR = os.path.join(FIXTURE_DIR, "request")
RESPONSE_DIR = os.path.join(FIXTURE_DIR, "response")


def load_data(path: str) -> Dict[str, str]:
    data = {}
    for f in os.listdir(path):
        p = os.path.join(path, f)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as r:
                data[f] = r.read()
    return data


@pytest.fixture
def requests():
    return load_data(REQUEST_DIR)


@pytest.fixture
def responses():
    return load_data(RESPONSE_DIR)


class TestParseResponse:
    def test_confirmation(self, responses):
        expected = ConfirmationResponse("{TARGET_URL}")
        j = responses["CONFIRMATION.json"]
        r = CONVERTER.from_json(j, ConfirmationResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), ConfirmationResponse)
        assert c == r and c is not r

    def test_configuration_initialize(self, responses):
        # Response for INITIALIZE is different than for PAGE
        expected = ConfigurationInitResponse(
            configuration_data=ConfigInitData(
                initialize=ConfigInit(
                    name="On When Open/Off When Shut WebHook App",
                    description="On When Open/Off When Shut WebHook App",
                    id="app",
                    permissions=[],
                    first_page_id="1",
                )
            )
        )
        j = responses["CONFIGURATION-INITIALIZE.json"]
        r = CONVERTER.from_json(j, ConfigurationInitResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), ConfigurationInitResponse)
        assert c == r and c is not r

    def test_configuration_page_only(self, responses):
        # Response for PAGE is different than for INITIALIZE
        # This tests the example for an only page (1 of 1)
        expected = ConfigurationPageResponse(
            configuration_data=ConfigPageData(
                page=ConfigPage(
                    page_id="1",
                    name="On When Open/Off When Shut WebHook App",
                    next_page_id=None,
                    previous_page_id=None,
                    complete=True,
                    sections=[
                        ConfigSection(
                            name="When this opens/closes...",
                            settings=[
                                DeviceSetting(
                                    id="contactSensor",
                                    name="Which contact sensor?",
                                    description="Tap to set",
                                    required=True,
                                    multiple=False,
                                    capabilities=["contactSensor"],
                                    permissions=["r"],
                                )
                            ],
                        ),
                        ConfigSection(
                            name="Turn on/off this light...",
                            settings=[
                                DeviceSetting(
                                    id="lightSwitch",
                                    name="Which switch?",
                                    description="Tap to set",
                                    required=True,
                                    multiple=False,
                                    capabilities=["switch"],
                                    permissions=["r", "x"],
                                )
                            ],
                        ),
                    ],
                )
            )
        )
        j = responses["CONFIGURATION-PAGE-only.json"]
        r = CONVERTER.from_json(j, ConfigurationPageResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), ConfigurationPageResponse)
        assert c == r and c is not r

    def test_configuration_page_1of2(self, responses):
        # Response for PAGE is different than for INITIALIZE
        # This tests the example for page 1 of 2
        expected = ConfigurationPageResponse(
            configuration_data=ConfigPageData(
                page=ConfigPage(
                    page_id="1",
                    name="On When Open/Off When Shut WebHook App",
                    next_page_id="2",
                    previous_page_id=None,
                    complete=False,
                    sections=[
                        ConfigSection(
                            name="When this opens/closes...",
                            settings=[
                                DeviceSetting(
                                    id="contactSensor",
                                    name="Which contact sensor?",
                                    description="Tap to set",
                                    required=True,
                                    multiple=False,
                                    capabilities=["contactSensor"],
                                    permissions=["r"],
                                )
                            ],
                        ),
                    ],
                )
            )
        )
        j = responses["CONFIGURATION-PAGE-1of2.json"]
        r = CONVERTER.from_json(j, ConfigurationPageResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), ConfigurationPageResponse)
        assert c == r and c is not r

    def test_install(self, responses):
        expected = InstallResponse()
        j = responses["INSTALL.json"]
        r = CONVERTER.from_json(j, InstallResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), InstallResponse)
        assert c == r and c is not r

    def test_update(self, responses):
        expected = UpdateResponse()
        j = responses["UPDATE.json"]
        r = CONVERTER.from_json(j, UpdateResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), UpdateResponse)
        assert c == r and c is not r

    def test_uninstall(self, responses):
        expected = UninstallResponse()
        j = responses["UNINSTALL.json"]
        r = CONVERTER.from_json(j, UninstallResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), UninstallResponse)
        assert c == r and c is not r

    def test_oauth_callback(self, responses):
        expected = OauthCallbackResponse()
        j = responses["OAUTH_CALLBACK.json"]
        r = CONVERTER.from_json(j, OauthCallbackResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), OauthCallbackResponse)
        assert c == r and c is not r

    def test_event(self, responses):
        expected = EventResponse()
        j = responses["EVENT.json"]
        r = CONVERTER.from_json(j, EventResponse)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), EventResponse)
        assert c == r and c is not r


class TestParseRequest:
    def test_confirmation(self, requests):
        expected = ConfirmationRequest(
            lifecycle=LifecyclePhase.CONFIRMATION,
            execution_id="8F8FA33E-2A5B-4BC5-826C-4B2AB73FE9DD",
            app_id="fd9949ee-a3bf-4069-b4b3-3e9c1c922e29",
            locale="en",
            version="0.1.0",
            confirmation_data=ConfirmationData(
                app_id="fd9949ee-a3bf-4069-b4b3-3e9c1c922e29", confirmation_url="{CONFIRMATION_URL}"
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        j = requests["CONFIRMATION.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

    def test_configuration_initialize(self, requests):
        expected = ConfigurationRequest(
            lifecycle=LifecyclePhase.CONFIGURATION,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            configuration_data=ConfigRequestData(
                installed_app_id="string",
                phase=ConfigPhase.INITIALIZE,
                page_id="string",
                previous_page_id="string",
                config={
                    "property1": [
                        DeviceConfigValue(
                            device_config=DeviceValue(
                                device_id="31192dc9-eb45-4d90-b606-21e9b66d8c2b",
                                component_id="main",
                            ),
                        )
                    ],
                    "property2": [
                        DeviceConfigValue(
                            device_config=DeviceValue(
                                device_id="31192dc9-eb45-4d90-b606-21e9b66d8c2b",
                                component_id="main",
                            ),
                        )
                    ],
                },
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        j = requests["CONFIGURATION-INITIALIZE.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

    def test_configuration_page(self, requests):
        # Note that the invalid "app" config item is ignored when we deserialize
        expected = ConfigurationRequest(
            lifecycle=LifecyclePhase.CONFIGURATION,
            execution_id="ce3975c1-0d03-3777-5250-0e61b15ad1d4",
            locale="en",
            version="0.1.0",
            configuration_data=ConfigRequestData(
                installed_app_id="58065067-52b9-49a5-a378-ce3871bc710b",
                phase=ConfigPhase.PAGE,
                page_id="2",
                previous_page_id="1",
                config={
                    "minutes": [
                        StringConfigValue(
                            string_config=StringValue(value="3"),
                        )
                    ],
                },
            ),
            settings={},
        )
        j = requests["CONFIGURATION-PAGE.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

    def test_install(self, requests):
        expected = InstallRequest(
            lifecycle=LifecyclePhase.INSTALL,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            install_data=InstallData(
                auth_token="string",
                refresh_token="string",
                installed_app=InstalledApp(
                    installed_app_id="d692699d-e7a6-400d-a0b7-d5be96e7a564",
                    location_id="e675a3d9-2499-406c-86dc-8a492a886494",
                    config={
                        "contactSensor": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                string_config=StringValue(value="5"),
                            )
                        ],
                    },
                    permissions=[
                        "r:devices:e457978e-5e37-43e6-979d-18112e12c961",
                        "r:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                        "x:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                    ],
                ),
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        j = requests["INSTALL.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

    def test_update(self, requests):
        expected = UpdateRequest(
            lifecycle=LifecyclePhase.UPDATE,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            update_data=UpdateData(
                auth_token="string",
                refresh_token="string",
                installed_app=InstalledApp(
                    installed_app_id="d692699d-e7a6-400d-a0b7-d5be96e7a564",
                    location_id="e675a3d9-2499-406c-86dc-8a492a886494",
                    config={
                        "contactSensor": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                string_config=StringValue(value="5"),
                            )
                        ],
                    },
                    permissions=[
                        "r:devices:e457978e-5e37-43e6-979d-18112e12c961",
                        "r:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                        "x:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                    ],
                ),
                previous_config={
                    "contactSensor": [
                        DeviceConfigValue(
                            device_config=DeviceValue(
                                device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                component_id="main",
                            ),
                        )
                    ],
                    "lightSwitch": [
                        DeviceConfigValue(
                            device_config=DeviceValue(
                                device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                component_id="main",
                            ),
                        )
                    ],
                    "minutes": [
                        StringConfigValue(
                            string_config=StringValue(value="5"),
                        )
                    ],
                },
                previous_permissions=[
                    "r:devices:e457978e-5e37-43e6-979d-18112e12c961",
                    "r:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                    "x:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                ],
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        j = requests["UPDATE.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

    def test_uninstall(self, requests):
        expected = UninstallRequest(
            lifecycle=LifecyclePhase.UNINSTALL,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            uninstall_data=UninstallData(
                installed_app=InstalledApp(
                    installed_app_id="d692699d-e7a6-400d-a0b7-d5be96e7a564",
                    location_id="e675a3d9-2499-406c-86dc-8a492a886494",
                    config={
                        "contactSensor": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                string_config=StringValue(value="5"),
                            )
                        ],
                    },
                    permissions=[
                        "r:devices:e457978e-5e37-43e6-979d-18112e12c961",
                        "r:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                        "x:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                    ],
                )
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        j = requests["UNINSTALL.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

    def test_oauth_callback(self, requests):
        expected = OauthCallbackRequest(
            lifecycle=LifecyclePhase.OAUTH_CALLBACK,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            o_auth_callback_data=OauthCallbackData(installed_app_id="string", url_path="string"),
        )
        j = requests["OAUTH_CALLBACK.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

    def test_event_device(self, requests):
        expected = EventRequest(
            lifecycle=LifecyclePhase.EVENT,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            event_data=EventData(
                auth_token="string",
                installed_app=InstalledApp(
                    installed_app_id="d692699d-e7a6-400d-a0b7-d5be96e7a564",
                    location_id="e675a3d9-2499-406c-86dc-8a492a886494",
                    config={
                        "contactSensor": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                string_config=StringValue(value="5"),
                            )
                        ],
                    },
                    permissions=[
                        "r:devices:e457978e-5e37-43e6-979d-18112e12c961",
                        "r:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                        "x:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                    ],
                ),
                events=[
                    Event(
                        event_type=EventType.DEVICE_EVENT,
                        device_event=DeviceEvent(
                            subscription_name="motion_sensors",
                            event_id="736e3903-001c-4d40-b408-ff40d162a06b",
                            location_id="499e28ba-b33b-49c9-a5a1-cce40e41f8a6",
                            device_id="6f5ea629-4c05-4a90-a244-cc129b0a80c3",
                            component_id="main",
                            capability="motionSensor",
                            attribute="motion",
                            value="active",
                            state_change=True,
                            data=None,
                        ),
                    )
                ],
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        j = requests["EVENT-DEVICE.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

    def test_event_timer(self, requests):
        expected = EventRequest(
            lifecycle=LifecyclePhase.EVENT,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            event_data=EventData(
                auth_token="string",
                installed_app=InstalledApp(
                    installed_app_id="d692699d-e7a6-400d-a0b7-d5be96e7a564",
                    location_id="e675a3d9-2499-406c-86dc-8a492a886494",
                    config={
                        "contactSensor": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                string_config=StringValue(value="5"),
                            )
                        ],
                    },
                    permissions=[
                        "r:devices:e457978e-5e37-43e6-979d-18112e12c961",
                        "r:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                        "x:devices:74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                    ],
                ),
                events=[
                    Event(
                        event_type=EventType.TIMER_EVENT,
                        timer_event=TimerEvent(
                            event_id="string",
                            name="lights_off_timeout",
                            type="CRON",
                            time=pendulum.datetime(2017, 9, 13, 4, 18, 12, microsecond=469000, tz="UTC"),
                            expression="string",
                        ),
                    )
                ],
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        j = requests["EVENT-TIMER.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r

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
    ConfigValueType,
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


class TestResponseRoundTrip:
    @pytest.mark.parametrize(
        "source,obj",
        [
            ("INSTALL", InstallResponse),
            ("UPDATE", UpdateResponse),
            ("UNINSTALL", UninstallResponse),
            ("OAUTH_CALLBACK", OauthCallbackResponse),
            ("EVENT", EventResponse),
        ],
    )
    def test_empty(self, source, obj, responses):
        # Most responses are empty, so we're just that we can generate and round-trip JSON as expected
        o = obj()
        j = responses["%s.json" % source]
        assert CONVERTER.from_json(j, obj) == o
        assert CONVERTER.from_json(CONVERTER.to_json(o), obj) == o

    def test_confirmation(self, responses):
        # Confirmation takes a single argument, which the example shows as "{TARGET_URL}"
        o = ConfirmationResponse("{TARGET_URL}")
        j = responses["CONFIRMATION.json"]
        assert CONVERTER.from_json(j, ConfirmationResponse) == o
        assert CONVERTER.from_json(CONVERTER.to_json(o), ConfirmationResponse) == o

    def test_configration_initialize(self, responses):
        # Response for INITIALIZE is different than for PAGE
        o = ConfigurationInitResponse(
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
        assert CONVERTER.from_json(j, ConfigurationInitResponse) == o
        assert CONVERTER.from_json(CONVERTER.to_json(o), ConfigurationInitResponse) == o

    def test_configuration_page_only(self, responses):
        # Response for PAGE is different than for INITIALIZE
        # This tests the example for an only page (1 of 1)
        o = ConfigurationPageResponse(
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
        assert CONVERTER.from_json(j, ConfigurationPageResponse) == o
        assert CONVERTER.from_json(CONVERTER.to_json(o), ConfigurationPageResponse) == o

    def test_configuration_page_1of2(self, responses):
        # Response for PAGE is different than for INITIALIZE
        # This tests the example for page 1 of 2
        o = ConfigurationPageResponse(
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
        assert CONVERTER.from_json(j, ConfigurationPageResponse) == o
        assert CONVERTER.from_json(CONVERTER.to_json(o), ConfigurationPageResponse) == o


class TestRequestRoundTrip:

    # This spot-checks that we get the right type from each example file and that we can round-trip it succesfully
    # Other tests below confirm that we are actually parsing each file properly

    @pytest.mark.parametrize(
        "source,obj",
        [
            ("CONFIRMATION", ConfirmationRequest),
            ("CONFIGURATION", ConfigurationRequest),
            ("INSTALL", InstallRequest),
            ("UPDATE", UpdateRequest),
            ("UNINSTALL", UninstallRequest),
            ("OAUTH_CALLBACK", OauthCallbackRequest),
            ("EVENT-DEVICE", EventRequest),
            ("EVENT-TIMER", EventRequest),
        ],
    )
    def test_round_trip(self, source, obj, requests):
        j = requests["%s.json" % source]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, obj)
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
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

    def test_configuration(self, requests):
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
                            value_type=ConfigValueType.DEVICE,
                            device_config=DeviceValue(
                                device_id="31192dc9-eb45-4d90-b606-21e9b66d8c2b",
                                component_id="main",
                            ),
                        )
                    ],
                    "property2": [
                        DeviceConfigValue(
                            value_type=ConfigValueType.DEVICE,
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
        j = requests["CONFIGURATION.json"]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert expected == r

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
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                value_type=ConfigValueType.STRING,
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
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                value_type=ConfigValueType.STRING,
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
                            value_type=ConfigValueType.DEVICE,
                            device_config=DeviceValue(
                                device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                component_id="main",
                            ),
                        )
                    ],
                    "lightSwitch": [
                        DeviceConfigValue(
                            value_type=ConfigValueType.DEVICE,
                            device_config=DeviceValue(
                                device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                component_id="main",
                            ),
                        )
                    ],
                    "minutes": [
                        StringConfigValue(
                            value_type=ConfigValueType.STRING,
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
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                value_type=ConfigValueType.STRING,
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
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                value_type=ConfigValueType.STRING,
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
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="e457978e-5e37-43e6-979d-18112e12c961",
                                    component_id="main",
                                ),
                            )
                        ],
                        "lightSwitch": [
                            DeviceConfigValue(
                                value_type=ConfigValueType.DEVICE,
                                device_config=DeviceValue(
                                    device_id="74aac3bb-91f2-4a88-8c49-ae5e0a234d76",
                                    component_id="main",
                                ),
                            )
                        ],
                        "minutes": [
                            StringConfigValue(
                                value_type=ConfigValueType.STRING,
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

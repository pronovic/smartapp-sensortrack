# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,invalid-name:

import os

import pendulum
import pytest

from sensortrack.lifecycle.converter import CONVERTER
from sensortrack.lifecycle.interface import (
    ConfigData,
    ConfigPhase,
    ConfigurationRequest,
    ConfigValueType,
    ConfirmationData,
    ConfirmationRequest,
    DeviceConfigValue,
    DeviceEvent,
    DeviceValue,
    Event,
    EventData,
    EventRequest,
    EventType,
    InstallData,
    InstalledApp,
    InstallRequest,
    LifecyclePhase,
    LifecycleRequest,
    OauthCallbackData,
    OauthCallbackRequest,
    StringConfigValue,
    StringValue,
    TimerEvent,
    UninstallData,
    UninstallRequest,
    UpdateData,
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


class TestParseRequestRoundTrip:

    # This spot-checks that we get the right type from each example file and that we can round-trip it succesfully
    # Other tests below confirm that we are actually parsing each file properly

    @pytest.mark.parametrize(
        "source,expected",
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
    def test_round_trip(self, source, expected, requests):
        j = requests["%s.json" % source]
        r = CONVERTER.from_json(j, LifecycleRequest)
        assert isinstance(r, expected)
        c = CONVERTER.from_json(CONVERTER.to_json(r), LifecycleRequest)
        assert c == r and c is not r


class TestParseRequestValues:
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
            configuration_data=ConfigData(
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

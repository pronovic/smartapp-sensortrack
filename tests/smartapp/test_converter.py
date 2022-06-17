# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,invalid-name,wildcard-import:

import os
from json import JSONDecodeError
from unittest.mock import patch

import pendulum
import pytest

from smartapp.converter import CONVERTER, deserialize_datetime, serialize_datetime
from smartapp.interface import *
from tests.testutil import load_data

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures/samples")
REQUEST_DIR = os.path.join(FIXTURE_DIR, "request")
RESPONSE_DIR = os.path.join(FIXTURE_DIR, "response")
SETTINGS_DIR = os.path.join(FIXTURE_DIR, "settings")

NOW = pendulum.datetime(2022, 6, 1, 2, 3, 4, microsecond=5, tz="UTC")


@pytest.fixture
def requests():
    return load_data(REQUEST_DIR)


@pytest.fixture
def responses():
    return load_data(RESPONSE_DIR)


@pytest.fixture
def settings():
    return load_data(SETTINGS_DIR)


def validate_json_roundtrip(json, expected, cls):
    """Validate a JSON round trip."""
    if json:
        obj = CONVERTER.from_json(json, cls)
        assert obj == expected
    converted = CONVERTER.from_json(CONVERTER.to_json(expected), cls)
    assert converted == expected and converted is not expected


def validate_yaml_roundtrip(yaml, expected, cls):
    """Validate a YAML round trip."""
    if yaml:
        obj = CONVERTER.from_yaml(yaml, cls)
        assert obj == expected
    converted = CONVERTER.from_yaml(CONVERTER.to_yaml(expected), cls)
    assert converted == expected and converted is not expected


class TestDatetime:
    @pytest.mark.parametrize(
        "datetime,expected",
        [
            (pendulum.datetime(2017, 9, 13, 4, 18, 12, microsecond=469000, tz="UTC"), "2017-09-13T04:18:12.469Z"),
            (pendulum.datetime(2017, 9, 13, 4, 18, 12, microsecond=0, tz="UTC"), "2017-09-13T04:18:12.000Z"),
            (pendulum.datetime(1970, 1, 1, 0, 0, 0, microsecond=0, tz="UTC"), "1970-01-01T00:00:00.000Z"),
        ],
    )
    def test_serialize_datetime(self, datetime, expected):
        assert serialize_datetime(datetime) == expected

    @patch("smartapp.converter.now")
    @pytest.mark.parametrize(
        "datetime,expected",
        [
            ("2017-09-13T04:18:12.469Z", pendulum.datetime(2017, 9, 13, 4, 18, 12, microsecond=469000, tz="UTC")),
            ("2017-09-13T04:18:12.000Z", pendulum.datetime(2017, 9, 13, 4, 18, 12, microsecond=0, tz="UTC")),
            ("2017-09-13T04:18:12Z", pendulum.datetime(2017, 9, 13, 4, 18, 12, microsecond=0, tz="UTC")),
            ("2022-06-16T15:17:24.883Z", pendulum.datetime(2022, 6, 16, 10, 17, 24, microsecond=883000, tz="America/Chicago")),
            ("2022-06-16T15:17:24.000Z", pendulum.datetime(2022, 6, 16, 10, 17, 24, microsecond=0, tz="America/Chicago")),
            ("2022-06-16T15:16:24Z", pendulum.datetime(2022, 6, 16, 10, 16, 24, microsecond=0, tz="America/Chicago")),
            ("1970-01-01T00:00:00.000Z", NOW),
            ("1970-01-01T00:00:00Z", NOW),
        ],
    )
    def test_deserialize_datetime(self, now, datetime, expected):
        now.return_value = NOW
        assert deserialize_datetime(datetime) == expected

    @pytest.mark.parametrize(
        "datetime",
        [
            "",  # empty
            "2017-09-13T04:18:12.469",  # no trailing Z
            "2017-09-13T04:18:12",  # no trailing Z
        ],
    )
    def test_deserialize_datetim_invalid(self, datetime):
        with pytest.raises(ValueError, match="Unknown datetime format"):
            deserialize_datetime(datetime)


class TestConvertSettings:
    def test_boolean(self, settings):
        json = settings["BOOLEAN.json"]
        expected = BooleanSetting(
            id="myBooleanSetting",
            name="True or false?",
            description="Tap to set",
            required=True,
            default_value="true",
        )
        validate_json_roundtrip(json, expected, BooleanSetting)
        validate_yaml_roundtrip(None, expected, BooleanSetting)

    def test_decimal(self, settings):
        json = settings["DECIMAL.json"]
        expected = DecimalSetting(
            id="myDecimalSetting",
            name="Enter a decimal value",
            description="Tap to set",
        )
        validate_json_roundtrip(json, expected, DecimalSetting)
        validate_yaml_roundtrip(None, expected, DecimalSetting)

    def test_device(self, settings):
        json = settings["DEVICE.json"]
        expected = DeviceSetting(
            id="contactSensor",
            name="Which contact sensor?",
            description="Tap to set",
            required=True,
            multiple=False,
            capabilities=["contactSensor"],
            permissions=["r"],
        )
        validate_json_roundtrip(json, expected, DeviceSetting)
        validate_yaml_roundtrip(None, expected, DeviceSetting)

    def test_email(self, settings):
        json = settings["EMAIL.json"]
        expected = EmailSetting(
            id="myEmailSetting",
            name="Enter an email address",
            description="Tap to set",
        )
        validate_json_roundtrip(json, expected, EmailSetting)
        validate_yaml_roundtrip(None, expected, EmailSetting)

    def test_enum(self, settings):
        json = settings["ENUM.json"]
        expected = EnumSetting(
            id="myEnumSetting",
            name="Choose what applies",
            description="Tap to set",
            required=True,
            multiple=True,
            options=[EnumOption(id="option-1", name="Option 1"), EnumOption(id="option-2", name="Option 2")],
        )
        validate_json_roundtrip(json, expected, EnumSetting)
        validate_yaml_roundtrip(None, expected, EnumSetting)

    def test_enum_group(self, settings):
        json = settings["ENUM-GROUP.json"]
        expected = EnumSetting(
            id="myGroupedEnumSetting",
            name="Choose what applies",
            description="Tap to set",
            required=True,
            multiple=True,
            grouped_options=[
                EnumOptionGroup(
                    name="Group 1", options=[EnumOption(id="option-1", name="Option 1"), EnumOption(id="option-2", name="Option 2")]
                ),
                EnumOptionGroup(
                    name="Group 2",
                    options=[
                        EnumOption(id="option-3", name="Option 3"),
                        EnumOption(id="option-4", name="Option 4"),
                        EnumOption(id="option-5", name="Option 5"),
                    ],
                ),
            ],
        )
        validate_json_roundtrip(json, expected, EnumSetting)
        validate_yaml_roundtrip(None, expected, EnumSetting)

    def test_icon(self, settings):
        json = settings["ICON.json"]
        expected = IconSetting(
            id="myIconInput",
            name="Some icon information",
            description="Some description",
            image="https://some-image-url",
        )
        validate_json_roundtrip(json, expected, IconSetting)
        validate_yaml_roundtrip(None, expected, IconSetting)

    def test_image(self, settings):
        json = settings["IMAGE.json"]
        expected = ImageSetting(
            id="myImageInput",
            name="Choose what applies",
            description="Tap to set",
            image="https://some-image-url",
        )
        validate_json_roundtrip(json, expected, ImageSetting)
        validate_yaml_roundtrip(None, expected, ImageSetting)

    def test_link(self, settings):
        json = settings["LINK.json"]
        expected = LinkSetting(
            id="myLinkSetting",
            name="Visit the following link",
            description="Tap to visit",
            url="https://some-site-url",
            image="https://some-image-url",
        )
        validate_json_roundtrip(json, expected, LinkSetting)
        validate_yaml_roundtrip(None, expected, LinkSetting)

    def test_number(self, settings):
        json = settings["NUMBER.json"]
        expected = NumberSetting(
            id="myNumberSetting",
            name="Enter a number",
            description="Tap to set",
        )
        validate_json_roundtrip(json, expected, NumberSetting)
        validate_yaml_roundtrip(None, expected, NumberSetting)

    # pylint: disable=line-too-long:
    def test_oauth(self, settings):
        json = settings["OAUTH.json"]
        expected = OauthSetting(
            id="myOauthSetting",
            name="Authenticate with the third party service",
            description="Tap to set",
            browser=False,
            url_template="http://www.some-third-party.com/oauth?param1=1&param2=2&callback=https%3A%2F%2Fapi.smartthings.com%2Foauth%2Fcallback",
        )
        validate_json_roundtrip(json, expected, OauthSetting)
        validate_yaml_roundtrip(None, expected, OauthSetting)

    def test_page(self, settings):
        json = settings["PAGE.json"]
        expected = PageSetting(
            id="myPageSetting",
            name="Choose what applies",
            description="Tap to set",
            page="page-id",
            image="https://some-image-url",
        )
        validate_json_roundtrip(json, expected, PageSetting)
        validate_yaml_roundtrip(None, expected, PageSetting)

    def test_paragraph(self, settings):
        json = settings["PARAGRAPH.json"]
        expected = ParagraphSetting(
            id="myParagraphSetting",
            name="Some information title",
            description="Some description",
            default_value="This is the information to display.",
        )
        validate_json_roundtrip(json, expected, ParagraphSetting)
        validate_yaml_roundtrip(None, expected, ParagraphSetting)

    def test_phone(self, settings):
        json = settings["PHONE.json"]
        expected = PhoneSetting(
            id="myPhoneSetting",
            name="Enter a phone number",
            description="Tap to set",
        )
        validate_json_roundtrip(json, expected, PhoneSetting)
        validate_yaml_roundtrip(None, expected, PhoneSetting)

    def test_text(self, settings):
        json = settings["TEXT.json"]
        expected = TextSetting(
            id="myTextSetting",
            name="Enter some text",
            description="Tap to set",
            required=True,
            default_value="Some default value",
        )
        validate_json_roundtrip(json, expected, TextSetting)
        validate_yaml_roundtrip(None, expected, TextSetting)

    def test_time(self, settings):
        json = settings["TIME.json"]
        expected = TimeSetting(
            id="myTimeInput",
            name="Choose a time",
            description="Tap to set",
        )
        validate_json_roundtrip(json, expected, TimeSetting)
        validate_yaml_roundtrip(None, expected, TimeSetting)


class TestStringSecrets:

    # Some requests contain secret tokens in the auth_token or refresh_token fields
    # These must not be included when turning the object into a string, which attrs handles with field(repr=False)

    @pytest.mark.parametrize(
        "source",
        [
            "INSTALL.json",
            "UPDATE.json",
            "EVENT-TIMER.json",
            "EVENT-DEVICE.json",
        ],
    )
    def test_secrets(self, requests, source):
        json = requests[source]
        request = CONVERTER.from_json(json, LifecycleRequest)
        for string in ["%s" % request, str(request), request.__repr__()]:
            print(string)
            assert "auth_token" not in string and "authTokenValue" not in string
            assert "refresh_token" not in string and "refreshTokenValue" not in string


class TestConvertResponses:
    def test_confirmation(self, responses):
        json = responses["CONFIRMATION.json"]
        expected = ConfirmationResponse(target_url="{TARGET_URL}")
        validate_json_roundtrip(json, expected, ConfirmationResponse)
        validate_yaml_roundtrip(None, expected, ConfirmationResponse)

    def test_configuration_initialize(self, responses):
        # Response for INITIALIZE is different than for PAGE
        json = responses["CONFIGURATION-INITIALIZE.json"]
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
        validate_json_roundtrip(json, expected, ConfigurationInitResponse)
        validate_yaml_roundtrip(None, expected, ConfigurationInitResponse)

    def test_configuration_page_only(self, responses):
        # Response for PAGE is different than for INITIALIZE
        # This tests the example for an only page (1 of 1)
        json = responses["CONFIGURATION-PAGE-only.json"]
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
        validate_json_roundtrip(json, expected, ConfigurationPageResponse)
        validate_yaml_roundtrip(None, expected, ConfigurationPageResponse)

    def test_configuration_page_1of2(self, responses):
        # Response for PAGE is different than for INITIALIZE
        # This tests the example for page 1 of 2
        json = responses["CONFIGURATION-PAGE-1of2.json"]
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
        validate_json_roundtrip(json, expected, ConfigurationPageResponse)
        validate_yaml_roundtrip(None, expected, ConfigurationPageResponse)

    def test_install(self, responses):
        json = responses["INSTALL.json"]
        expected = InstallResponse()
        validate_json_roundtrip(json, expected, InstallResponse)
        validate_yaml_roundtrip(None, expected, InstallResponse)

    def test_update(self, responses):
        json = responses["UPDATE.json"]
        expected = UpdateResponse()
        validate_json_roundtrip(json, expected, UpdateResponse)
        validate_yaml_roundtrip(None, expected, UpdateResponse)

    def test_uninstall(self, responses):
        json = responses["UNINSTALL.json"]
        expected = UninstallResponse()
        validate_json_roundtrip(json, expected, UninstallResponse)
        validate_yaml_roundtrip(None, expected, UninstallResponse)

    def test_oauth_callback(self, responses):
        json = responses["OAUTH_CALLBACK.json"]
        expected = OauthCallbackResponse()
        validate_json_roundtrip(json, expected, OauthCallbackResponse)
        validate_yaml_roundtrip(None, expected, OauthCallbackResponse)

    def test_event(self, responses):
        json = responses["EVENT.json"]
        expected = EventResponse()
        validate_json_roundtrip(json, expected, EventResponse)
        validate_yaml_roundtrip(None, expected, EventResponse)


class TestConvertRequests:
    def test_invalid_json(self):
        # This is not a valid JSON string
        with pytest.raises(JSONDecodeError):
            CONVERTER.from_json("*(&)(&_)()", LifecycleRequest)

    def test_mismatch_json(self):
        # This is valid JSON, just not valid LifecycleRequest
        with pytest.raises(ValueError):
            CONVERTER.from_json('{"hello": "there"}', LifecycleRequest)

    def test_confirmation(self, requests):
        json = requests["CONFIRMATION.json"]
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
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)

    def test_configuration_initialize(self, requests):
        json = requests["CONFIGURATION-INITIALIZE.json"]
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
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)

    def test_configuration_page(self, requests):
        # Note that the invalid "app" config item is ignored when we deserialize
        json = requests["CONFIGURATION-PAGE.json"]
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
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)

    def test_install(self, requests):
        json = requests["INSTALL.json"]
        expected = InstallRequest(
            lifecycle=LifecyclePhase.INSTALL,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            install_data=InstallData(
                auth_token="authTokenValue",
                refresh_token="refreshTokenValue",
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
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)

    def test_update(self, requests):
        json = requests["UPDATE.json"]
        expected = UpdateRequest(
            lifecycle=LifecyclePhase.UPDATE,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            update_data=UpdateData(
                auth_token="authTokenValue",
                refresh_token="refreshTokenValue",
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
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)

    def test_uninstall(self, requests):
        json = requests["UNINSTALL.json"]
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
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)

    def test_oauth_callback(self, requests):
        json = requests["OAUTH_CALLBACK.json"]
        expected = OauthCallbackRequest(
            lifecycle=LifecyclePhase.OAUTH_CALLBACK,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            o_auth_callback_data=OauthCallbackData(installed_app_id="string", url_path="string"),
        )
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)

    def test_event_device(self, requests):
        json = requests["EVENT-DEVICE.json"]
        expected = EventRequest(
            lifecycle=LifecyclePhase.EVENT,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            event_data=EventData(
                auth_token="authTokenValue",
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
                        device_event={
                            "subscriptionName": "motion_sensors",
                            "eventId": "736e3903-001c-4d40-b408-ff40d162a06b",
                            "locationId": "499e28ba-b33b-49c9-a5a1-cce40e41f8a6",
                            "deviceId": "6f5ea629-4c05-4a90-a244-cc129b0a80c3",
                            "componentId": "main",
                            "capability": "motionSensor",
                            "attribute": "motion",
                            "value": "active",
                            "stateChange": True,
                        },
                    )
                ],
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)

    def test_event_timer(self, requests):
        json = requests["EVENT-TIMER.json"]
        expected = EventRequest(
            lifecycle=LifecyclePhase.EVENT,
            execution_id="b328f242-c602-4204-8d73-33c48ae180af",
            locale="en",
            version="1.0.0",
            event_data=EventData(
                auth_token="authTokenValue",
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
                        timer_event={
                            "eventId": "string",
                            "name": "lights_off_timeout",
                            "type": "CRON",
                            "time": "2017-09-13T04:18:12.469Z",
                            "expression": "string",
                        },
                    )
                ],
            ),
            settings={
                "property1": "string",
                "property2": "string",
            },
        )
        validate_json_roundtrip(json, expected, LifecycleRequest)
        validate_yaml_roundtrip(None, expected, LifecycleRequest)


class TestConvertSmartAppDispatcherConfig:
    def test_config(self):
        expected = SmartAppDispatcherConfig(
            check_signatures=True,
            clock_skew_sec=1234,
            keyserver_url="https://whatever.com",
            log_json=False,
        )
        validate_json_roundtrip(None, expected, SmartAppDispatcherConfig)
        validate_yaml_roundtrip(None, expected, SmartAppDispatcherConfig)


class TestConvertSmartAppDefinition:
    def test_definition(self):
        # SmartAppDefinition isn't part of the SmartThings interface, but we support serializing/deserializing it
        expected = SmartAppDefinition(
            id="id",
            name="name",
            description="description",
            target_url="target_url",
            permissions=["permission"],
            config_pages=[
                SmartAppConfigPage(
                    page_name="First page",
                    sections=[
                        ConfigSection(
                            name="Section 1",
                            settings=[
                                ParagraphSetting(
                                    id="paragraph-id",
                                    name="paragraph-name",
                                    description="paragraph-description",
                                    default_value="paragraph-text",
                                ),
                            ],
                        )
                    ],
                ),
                SmartAppConfigPage(
                    page_name="Second page",
                    sections=[
                        ConfigSection(
                            name="Section 2",
                            settings=[
                                DecimalSetting(
                                    id="decimal-id",
                                    name="decimal-name",
                                    description="decimal-description",
                                    required=False,
                                ),
                            ],
                        )
                    ],
                ),
            ],
        )
        validate_json_roundtrip(None, expected, SmartAppDefinition)
        validate_yaml_roundtrip(None, expected, SmartAppDefinition)

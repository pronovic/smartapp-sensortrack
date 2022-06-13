# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,wildcard-import:

import os
from unittest.mock import MagicMock, patch

import pytest

from smartapp.converter import CONVERTER
from smartapp.dispatcher import (
    SmartAppConfigPage,
    SmartAppDefinition,
    SmartAppDispatcher,
    SmartAppDispatcherConfig,
    SmartAppEventHandler,
)
from smartapp.interface import *
from tests.testutil import load_data

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures/samples")
REQUEST_DIR = os.path.join(FIXTURE_DIR, "request")

CLOCK_SKEW_SEC = 555
CORRELATION = "AAAA"
HEADERS = {"x-st-correlation": CORRELATION}


@pytest.fixture
def requests():
    return load_data(REQUEST_DIR)


@pytest.fixture
def definition():
    return SmartAppDefinition(
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


@pytest.fixture
def event_handler() -> SmartAppEventHandler:
    return MagicMock()


@pytest.fixture
def dispatcher(definition: SmartAppDefinition, event_handler: SmartAppEventHandler) -> SmartAppDispatcher:
    return SmartAppDispatcher(
        definition=definition,
        event_handler=event_handler,
        config=SmartAppDispatcherConfig(check_signatures=False, clock_skew_sec=CLOCK_SKEW_SEC),
    )


@pytest.fixture
def dispatcher_with_check(definition: SmartAppDefinition, event_handler: SmartAppEventHandler) -> SmartAppDispatcher:
    return SmartAppDispatcher(
        definition=definition,
        event_handler=event_handler,
        config=SmartAppDispatcherConfig(check_signatures=True, clock_skew_sec=CLOCK_SKEW_SEC),
    )


# noinspection PyUnresolvedReferences
class TestSmartAppDispatcher:
    def test_json_exception(self, dispatcher):
        # all of the requests have the same behavior, so we just check it once
        with pytest.raises(BadRequestError):
            dispatcher.dispatch(headers=HEADERS, request_json="bogus")

    def test_handler_internal_error(self, requests, dispatcher):
        # all of the requests have the same behavior, so we just check it once
        request_json = requests["CONFIRMATION.json"]
        dispatcher.event_handler.handle_confirmation.side_effect = Exception("Hello")
        with pytest.raises(InternalError):
            dispatcher.dispatch(headers=HEADERS, request_json=request_json)

    @patch("smartapp.dispatcher.check_signature")
    def test_disabled_signature(self, check_signature, requests, dispatcher):
        # all of the requests have the same behavior, so we just check it once
        request_json = requests["CONFIRMATION.json"]
        dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        check_signature.assert_not_called()

    @patch("smartapp.dispatcher.check_signature")
    def test_enabled_signature(self, check_signature, requests, dispatcher_with_check):
        # all of the requests have the same behavior, so we just check it once
        request_json = requests["CONFIRMATION.json"]
        dispatcher_with_check.dispatch(headers=HEADERS, request_json=request_json)
        check_signature.assert_called_once_with(CORRELATION, HEADERS, request_json, CLOCK_SKEW_SEC)

    @patch("smartapp.dispatcher.check_signature")
    def test_bad_signature(self, check_signature, requests, dispatcher_with_check):
        # all of the requests have the same behavior, so we just check it once
        request_json = requests["CONFIRMATION.json"]
        check_signature.side_effect = SignatureError("Hello")  # this what would be thrown, so make sure it comes through
        with pytest.raises(SignatureError):
            dispatcher_with_check.dispatch(headers=HEADERS, request_json=request_json)
        check_signature.assert_called_once_with(CORRELATION, HEADERS, request_json, CLOCK_SKEW_SEC)

    def test_confirmation(self, requests, dispatcher):
        request_json = requests["CONFIRMATION.json"]
        request = CONVERTER.from_json(request_json, ConfirmationRequest)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(ConfirmationResponse(target_url="target_url"))
        dispatcher.event_handler.handle_confirmation.assert_called_once_with(CORRELATION, request)

    def test_install(self, requests, dispatcher):
        request_json = requests["INSTALL.json"]
        request = CONVERTER.from_json(request_json, InstallRequest)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(InstallResponse())
        dispatcher.event_handler.handle_install.assert_called_once_with(CORRELATION, request)

    def test_update(self, requests, dispatcher):
        request_json = requests["UPDATE.json"]
        request = CONVERTER.from_json(request_json, UpdateRequest)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(UpdateResponse())
        dispatcher.event_handler.handle_update.assert_called_once_with(CORRELATION, request)

    def test_uninstall(self, requests, dispatcher):
        request_json = requests["UNINSTALL.json"]
        request = CONVERTER.from_json(request_json, UninstallRequest)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(UninstallResponse())
        dispatcher.event_handler.handle_uninstall.assert_called_once_with(CORRELATION, request)

    def test_oauth_callback(self, requests, dispatcher):
        request_json = requests["OAUTH_CALLBACK.json"]
        request = CONVERTER.from_json(request_json, OauthCallbackRequest)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(OauthCallbackResponse())
        dispatcher.event_handler.handle_oauth_callback.assert_called_once_with(CORRELATION, request)

    def test_event(self, requests, dispatcher):
        request_json = requests["EVENT-DEVICE.json"]
        request = CONVERTER.from_json(request_json, EventRequest)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(EventResponse())
        dispatcher.event_handler.handle_event.assert_called_once_with(CORRELATION, request)

    def test_configuration_initialize(self, dispatcher):
        request = ConfigurationRequest(
            lifecycle=LifecyclePhase.CONFIGURATION,
            execution_id="execution_id",
            locale="locale",
            version="version",
            configuration_data=ConfigRequestData(
                installed_app_id="installed_app_id",
                phase=ConfigPhase.INITIALIZE,
                page_id="",
                previous_page_id="",
                config={},
            ),
        )
        response = ConfigurationInitResponse(
            configuration_data=ConfigInitData(
                # this is all from the provided SmartApp definition
                initialize=ConfigInit(
                    id="id",
                    name="name",
                    description="description",
                    permissions=["permission"],
                    first_page_id="1",
                )
            )
        )
        request_json = CONVERTER.to_json(request)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(response)
        dispatcher.event_handler.handle_configuration.assert_called_once_with(CORRELATION, request)

    def test_configuration_page_1of2(self, dispatcher):
        request = ConfigurationRequest(
            lifecycle=LifecyclePhase.CONFIGURATION,
            execution_id="execution_id",
            locale="locale",
            version="version",
            configuration_data=ConfigRequestData(
                installed_app_id="installed_app_id",
                phase=ConfigPhase.PAGE,
                page_id="1",
                previous_page_id="",
                config={},  # TODO: not 100% clear what comes across in these page requests, examples are odd
            ),
        )
        response = ConfigurationPageResponse(
            configuration_data=ConfigPageData(
                # most of this comes from the provided SmartApp definition, but some is derived
                page=ConfigPage(
                    page_id="1",
                    name="First page",
                    previous_page_id=None,
                    next_page_id="2",
                    complete=False,
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
                )
            )
        )
        request_json = CONVERTER.to_json(request)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(response)
        dispatcher.event_handler.handle_configuration.assert_called_once_with(CORRELATION, request)

    def test_configuration_page_2of2(self, dispatcher):
        request = ConfigurationRequest(
            lifecycle=LifecyclePhase.CONFIGURATION,
            execution_id="execution_id",
            locale="locale",
            version="version",
            configuration_data=ConfigRequestData(
                installed_app_id="installed_app_id",
                phase=ConfigPhase.PAGE,
                page_id="2",
                previous_page_id="",
                config={},  # TODO: not 100% clear what comes across in these page requests, examples are odd
            ),
        )
        response = ConfigurationPageResponse(
            configuration_data=ConfigPageData(
                # most of this comes from the provided SmartApp definition, but some is derived
                page=ConfigPage(
                    page_id="2",
                    name="Second page",
                    previous_page_id="1",
                    next_page_id=None,
                    complete=True,
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
                )
            )
        )
        request_json = CONVERTER.to_json(request)
        response_json = dispatcher.dispatch(headers=HEADERS, request_json=request_json)
        assert response_json == CONVERTER.to_json(response)
        dispatcher.event_handler.handle_configuration.assert_called_once_with(CORRELATION, request)

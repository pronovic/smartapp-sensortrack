# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,invalid-name,wildcard-import:
import pytest

from smartapp.interface import *


class TestExceptions:
    @pytest.mark.parametrize(
        "exception",
        [
            SmartAppError,
            InternalError,
            BadRequestError,
            SignatureError,
        ],
    )
    def test_exceptions(self, exception):
        e = exception("message")
        assert e.message == "message"
        assert e.correlation_id is None
        assert isinstance(e, SmartAppError)
        e = exception("message", "id")
        assert e.message == "message"
        assert e.correlation_id == "id"
        assert isinstance(e, SmartAppError)


class TestSmartAppRequestContext:
    def test_context(self):
        context = SmartAppRequestContext(
            headers={"authorization": "token", "x-st-correlation": "correlation", "another": "value"},
            body="thebody",
        )
        assert context.correlation_id == "correlation"

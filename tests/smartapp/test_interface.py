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
            method="POST",
            path="/the/path/to/whatever",
            headers={"authorization": "token", "x-st-correlation": "correlation", "another": "value"},
            body="thebody",
        )
        assert context.request_target == "post /the/path/to/whatever"
        assert context.authorization == "token"
        assert context.correlation_id == "correlation"
        assert context.header("(request-target)") == "post /the/path/to/whatever"
        assert context.header("authorization") == "token"
        assert context.header("x-st-correlation") == "correlation"
        assert context.header("bogus") is None
        assert context.all_headers(("authorization", "bogus")) == {"authorization": "token", "bogus": None}

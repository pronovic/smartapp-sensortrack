# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import codecs
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from influxdb_client.client.exceptions import InfluxDBError
from smartapp.interface import BadRequestError, InternalError, SignatureError, SmartAppRequestContext

from sensortrack.rest import RestClientError
from sensortrack.server import (
    API,
    API_VERSION,
    bad_request_handler,
    exception_handler,
    influxdb_error_handler,
    rest_client_error_handler,
    signature_error_handler,
    smartapp_error_handler,
)

CLIENT = TestClient(API)


class TestErrorHandlers:
    pytestmark = pytest.mark.asyncio

    async def test_bad_request_handler(self):
        e = BadRequestError("hello")
        response = await bad_request_handler(None, e)
        assert response.status_code == 400

    async def test_signature_error_handler(self):
        e = SignatureError("hello")
        response = await signature_error_handler(None, e)
        assert response.status_code == 401

    async def test_smartapp_error_handler(self):
        e = InternalError("hello")
        response = await smartapp_error_handler(None, e)
        assert response.status_code == 500

    async def test_rest_client_error_handler(self):
        e = RestClientError("hello")
        response = await rest_client_error_handler(None, e)
        assert response.status_code == 500

    async def test_influxdb_error_handler(self):
        e = InfluxDBError(message="hello")
        response = await influxdb_error_handler(None, e)
        assert response.status_code == 500

    async def test_exception_handler(self):
        e = Exception("hello")
        response = await exception_handler(None, e)
        assert response.status_code == 500


class TestRoutes:
    def test_health(self):
        response = CLIENT.get(url="/health")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    @patch("sensortrack.server.metadata_version")
    def test_version(self, metadata_version):
        metadata_version.return_value = "xxx"
        response = CLIENT.get(url="/version")
        assert response.status_code == 200
        assert response.json() == {"package": "xxx", "api": API_VERSION}

    @patch("sensortrack.server.dispatcher")
    def test_smartapp(self, d):
        d.return_value = MagicMock(dispatch=MagicMock(return_value="result"))
        response = CLIENT.post(url="/smartapp", headers={"a": "b"}, content="body")
        assert response.status_code == 200
        assert codecs.decode(response.content) == "result"
        assert response.headers["content-type"] == "application/json"
        d.return_value.dispatch.assert_called_once()
        (_, kwargs) = d.return_value.dispatch.call_args  # needed because FastAPI enhances the headers; we can't check equality
        context: SmartAppRequestContext = kwargs["context"]
        assert context.headers["a"] == "b"  # just make sure our headers get passed, among others
        assert context.body == "body"

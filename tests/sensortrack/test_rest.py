# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock

import pytest
from requests.exceptions import HTTPError

from sensortrack.rest import RestClientError, raise_for_status


class TestFunctions:
    def test_raise_for_status(self):
        request = MagicMock(body="request")
        response = MagicMock(request=request, text="response")
        response.raise_for_status = MagicMock()
        response.raise_for_status.side_effect = HTTPError("hello")
        with pytest.raises(RestClientError) as e:
            raise_for_status(response)
        assert e.value.request_body == "request"
        assert e.value.response_body == "response"

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import patch

import pytest

from sensortrack.config import ConfigError, InfluxDbConfig, ServerConfig, SmartThingsApiConfig, config, reset
from smartapp.interface import SmartAppDispatcherConfig


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "config", filename)


APPLICATION_YAML = fixture("application.yaml")
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_ORG = "iot"
INFLUXDB_TOKEN = "token"
INFLUXDB_BUCKET = "metrics"


class TestConfig:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Reset singleton before and after tests."""
        reset()
        yield
        reset()

    @patch.dict(
        os.environ,
        {
            "SENSORTRACK_CONFIG_PATH": APPLICATION_YAML,
            "SENSORTRACK_INFLUXDB_URL": INFLUXDB_URL,
            "SENSORTRACK_INFLUXDB_ORG": INFLUXDB_ORG,
            "SENSORTRACK_INFLUXDB_TOKEN": INFLUXDB_TOKEN,
            "SENSORTRACK_INFLUXDB_BUCKET": INFLUXDB_BUCKET,
        },
        clear=True,
    )
    def test_config_env(self):
        result = config()
        TestConfig._validate_config(result)

    @patch.dict(
        os.environ,
        {
            "SENSORTRACK_INFLUXDB_URL": INFLUXDB_URL,
            "SENSORTRACK_INFLUXDB_ORG": INFLUXDB_ORG,
            "SENSORTRACK_INFLUXDB_TOKEN": INFLUXDB_TOKEN,
            "SENSORTRACK_INFLUXDB_BUCKET": INFLUXDB_BUCKET,
        },
        clear=True,
    )
    def test_config_path(self):
        result = config(config_path=APPLICATION_YAML)
        TestConfig._validate_config(result)

    @patch.dict(
        os.environ,
        {
            "SENSORTRACK_INFLUXDB_URL": INFLUXDB_URL,
            "SENSORTRACK_INFLUXDB_ORG": INFLUXDB_ORG,
            "SENSORTRACK_INFLUXDB_TOKEN": INFLUXDB_TOKEN,
            "SENSORTRACK_INFLUXDB_BUCKET": INFLUXDB_BUCKET,
        },
        clear=True,
    )
    def test_config_env_no_var(self):
        with pytest.raises(ConfigError, match=r"Server is not properly configured, no \$SENSORTRACK_CONFIG_PATH found"):
            config()

    @patch.dict(
        os.environ,
        {
            "SENSORTRACK_CONFIG_PATH": "bogus",
            "SENSORTRACK_INFLUXDB_URL": INFLUXDB_URL,
            "SENSORTRACK_INFLUXDB_ORG": INFLUXDB_ORG,
            "SENSORTRACK_INFLUXDB_TOKEN": INFLUXDB_TOKEN,
            "SENSORTRACK_INFLUXDB_BUCKET": INFLUXDB_BUCKET,
        },
        clear=True,
    )
    def test_config_env_not_found(self):
        with pytest.raises(ConfigError, match=r"Server configuration is not readable: bogus"):
            config()

    @staticmethod
    def _validate_config(result):
        assert result == ServerConfig(
            dispatcher=SmartAppDispatcherConfig(
                check_signatures=True,
                clock_skew_sec=300,
                keyserver_url="https://key.smartthings.com",
                log_json=False,
            ),
            smartthings=SmartThingsApiConfig(
                base_url="https://api.smartthings.com",
            ),
            influxdb=InfluxDbConfig(
                url=INFLUXDB_URL,
                org=INFLUXDB_ORG,
                token=INFLUXDB_TOKEN,
                bucket=INFLUXDB_BUCKET,
            ),
        )

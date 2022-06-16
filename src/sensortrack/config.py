# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Server configuration
"""
import os
from os import R_OK, access
from os.path import isfile
from typing import Optional

from attrs import frozen

from smartapp.converter import StandardConverter

# We read this environment variable to find the server configuration YAML file on disk
from smartapp.interface import SmartAppDispatcherConfig

CONFIG_VAR = "SENSORTRACK_CONFIG_PATH"


@frozen
class ConfigError(Exception):
    """An error related to configuration."""

    message: str


@frozen
class SmartThingsApiConfig:
    """SmartThings API configuration."""

    base_url: str


@frozen
class InfluxDbConfig:
    """InfluxDB configuration."""

    url: str
    org: str
    token: str
    bucket: str


@frozen
class ServerConfig:
    """Server configuration."""

    dispatcher: SmartAppDispatcherConfig
    smartthings: SmartThingsApiConfig
    influxdb: InfluxDbConfig


_CONFIG: Optional[ServerConfig] = None
_CONVERTER = StandardConverter()


def _replace_envvars(source: str) -> str:
    """Replace constructs like {VAR} with environment variables."""
    return source.format(**os.environ)


def _load_config(config_path: Optional[str] = None) -> ServerConfig:
    """Load server configuration from disk, substituting environment variables of the form {VAR}."""
    if not config_path:
        config_path = os.environ[CONFIG_VAR] if CONFIG_VAR in os.environ else None
        if not config_path:
            raise ConfigError("Server is not properly configured, no $%s found" % CONFIG_VAR)
    if not (isfile(config_path) and access(config_path, R_OK)):
        raise ConfigError("Server configuration is not readable: %s" % config_path)
    with open(config_path, "r", encoding="utf8") as fp:
        normalized = _replace_envvars(fp.read())
        return _CONVERTER.from_yaml(normalized, ServerConfig)


def reset() -> None:
    """Reset the config singleton, forcing it to be reloaded when next used."""
    global _CONFIG  # pylint: disable=global-statement
    _CONFIG = None


def config(config_path: Optional[str] = None) -> ServerConfig:
    """Retrieve server configuration, loading it from disk once and caching it."""
    global _CONFIG  # pylint: disable=global-statement
    if _CONFIG is None:
        _CONFIG = _load_config(config_path)
    return _CONFIG

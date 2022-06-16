# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Converter to serialize and deserialize lifecycle objects to various formats.
"""
import json
from typing import Any, Dict, Type, TypeVar

import yaml
from attrs import fields, has
from cattrs import GenConverter
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override
from pendulum import from_format, now
from pendulum.datetime import DateTime

from .interface import (
    CONFIG_SETTING_BY_TYPE,
    CONFIG_VALUE_BY_TYPE,
    REQUEST_BY_PHASE,
    ConfigSetting,
    ConfigSettingType,
    ConfigValue,
    ConfigValueType,
    LifecyclePhase,
    LifecycleRequest,
)

DATETIME_ZONE = "UTC"

DATETIME_SEC_EPOCH = "1970-01-01T00:00:00Z"  # date of the UNIX epoch, which sometimes seem to mean "no date"
DATETIME_SEC_LEN = len("YYYY-MM-DDTHH:MM:SSZ")  # like "2017-09-13T04:18:12Z"
DATETIME_SEC_FORMAT = "YYYY-MM-DD[T]HH:mm:ss[Z]"

DATETIME_MS_EPOCH = "1970-01-01T00:00:00.000Z"  # date of the UNIX epoch, which sometimes seem to mean "no date"
DATETIME_MS_LEN = len("YYYY-MM-DDTHH:MM:SS.SSSZ")  # like "2017-09-13T04:18:12.992Z"
DATETIME_MS_FORMAT = "YYYY-MM-DD[T]HH:mm:ss.SSS[Z]"

T = TypeVar("T")  # pylint: disable=invalid-name:


def serialize_datetime(datetime: DateTime) -> str:
    """Serialize a DateTime to a string."""
    # Note that we always use the full millisecond timestamp here and always convert to UTC
    return datetime.in_timezone(DATETIME_ZONE).format(DATETIME_MS_FORMAT)  # type: ignore


def deserialize_datetime(datetime: str) -> DateTime:
    """Deserialize a string into a DateTime."""
    # Dates from SmartThings are not as reliable as I had hoped.  The samples show a
    # format including milliseconds.  Actual data (at least sometimes) comes without
    # milliseconds.  Further, some requests come with a UNIX epoch date (1970-01-01) which
    # I guess is probably what happens when no date was set by the device.  I'm choosing
    # to interpret that as "now".
    if datetime in (DATETIME_MS_EPOCH, DATETIME_SEC_EPOCH):
        return now()
    elif len(datetime) == DATETIME_MS_LEN:
        return from_format(datetime, DATETIME_MS_FORMAT, tz=DATETIME_ZONE)
    elif len(datetime) == DATETIME_SEC_LEN:
        return from_format(datetime, DATETIME_SEC_FORMAT, tz=DATETIME_ZONE)
    else:
        raise ValueError("Unknown datetime format: %s" % datetime)


# noinspection PyMethodMayBeStatic
class StandardConverter(GenConverter):
    """
    Standard cattrs converter supporting both JSON and YAML and using camelCase for fields.
    """

    # Note: we need to inherit from GenConverter and not Converter because we use PEP563 (postponed) annotations
    # See: https://stackoverflow.com/a/72539298/2907667 and https://github.com/python-attrs/cattrs/issues/41

    # The factory hooks convert snake case to camel case
    # See: https://cattrs.readthedocs.io/en/latest/usage.html#using-factory-hooks

    def __init__(self) -> None:
        super().__init__()
        self.register_unstructure_hook_factory(has, self._unstructure_camel_case)
        self.register_structure_hook_factory(has, self._structure_camel_case)

    def to_json(self, obj: Any) -> str:
        """Serialize an object to JSON."""
        return json.dumps(self.unstructure(obj), indent="  ")

    def from_json(self, data: str, cls: Type[T]) -> T:
        """Deserialize an object from JSON."""
        return self.structure(json.loads(data), cls)

    def to_yaml(self, obj: Any) -> str:
        """Serialize an object to YAML."""
        return yaml.safe_dump(self.unstructure(obj), sort_keys=False)  # type: ignore

    def from_yaml(self, data: str, cls: Type[T]) -> T:
        """Deserialize an object from YAML."""
        return self.structure(yaml.safe_load(data), cls)

    def _to_camel_case(self, name: str) -> str:
        """Convert a snake_case attribute name to camelCase instead."""
        components = name.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def _unstructure_camel_case(self, cls):  # type: ignore
        """Automatic snake_case to camelCase conversion when serializing any class."""
        return make_dict_unstructure_fn(cls, self, **{a.name: override(rename=self._to_camel_case(a.name)) for a in fields(cls)})

    def _structure_camel_case(self, cls):  # type: ignore
        """Automatic snake_case to camelCase conversion when deserializing any class."""
        return make_dict_structure_fn(cls, self, **{a.name: override(rename=self._to_camel_case(a.name)) for a in fields(cls)})


# noinspection PyMethodMayBeStatic
class SmartAppConverter(StandardConverter):
    """
    Cattrs converter to serialize/deserialize SmartApp-related classes, supporting both JSON and YAML.
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_unstructure_hook(DateTime, self._unstructure_datetime)
        self.register_structure_hook(DateTime, self._structure_datetime)
        self.register_structure_hook(ConfigValue, self._structure_config_value)
        self.register_structure_hook(ConfigSetting, self._structure_config_setting)
        self.register_structure_hook(LifecycleRequest, self._structure_request)

    def _unstructure_datetime(self, datetime: DateTime) -> str:
        """Serialize a DateTime to a string."""
        return serialize_datetime(datetime)

    def _structure_datetime(self, datetime: str, _: Type[DateTime]) -> DateTime:
        """Deserialize a string into a DateTime."""
        return deserialize_datetime(datetime)

    def _structure_config_value(self, data: Dict[str, Any], _: Type[ConfigValue]) -> ConfigValue:
        """Deserialize input data into a ConfigValue of the proper type."""
        try:
            value_type = ConfigValueType[data["valueType"]]
            return self.structure(data, CONFIG_VALUE_BY_TYPE[value_type])
        except KeyError as e:
            raise ValueError("Unknown config value type") from e

    def _structure_config_setting(self, data: Dict[str, Any], _: Type[ConfigSetting]) -> ConfigSetting:
        """Deserialize input data into a ConfigSetting of the proper type."""
        try:
            value_type = ConfigSettingType[data["type"]]
            return self.structure(data, CONFIG_SETTING_BY_TYPE[value_type])  # type: ignore
        except KeyError as e:
            raise ValueError("Unknown config setting type") from e

    def _structure_request(self, data: Dict[str, Any], _: Type[LifecycleRequest]) -> LifecycleRequest:
        """Deserialize input data into a LifecycleRequest of the proper type."""
        try:
            phase = LifecyclePhase[data["lifecycle"]]
            return self.structure(data, REQUEST_BY_PHASE[phase])  # type: ignore
        except KeyError as e:
            raise ValueError("Unknown lifecycle phase") from e


CONVERTER = SmartAppConverter()

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Converter to serialize and deserialize lifecycle objects to various formats.
"""

import json
from typing import Any, Dict, Type

from attrs import fields, has
from cattrs import GenConverter
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override
from pendulum import from_format
from pendulum.datetime import DateTime

from .interface import CONFIG_VALUE_BY_TYPE, REQUEST_BY_PHASE, ConfigValue, ConfigValueType, LifecyclePhase, LifecycleRequest

TIMESTAMP_FORMAT = "YYYY-MM-DD[T]HH:mm:ss.SSS[Z]"  # example: "2017-09-13T04:18:12.469Z"
TIMESTAMP_ZONE = "UTC"


# noinspection PyMethodMayBeStatic
class LifecycleConverter(GenConverter):
    """
    Cattrs converter to serialize/deserialize the lifestyle class structure, supporting both JSON and YAML.
    """

    # Note: we need to use GenConverter and not Converter because we use PEP563 (postponed) annotations
    # See: https://stackoverflow.com/a/72539298/2907667 and https://github.com/python-attrs/cattrs/issues/41

    # The factory hooks convert snake case to camel case, so we can use normal coding standards with SmartThings JSON
    # See: https://cattrs.readthedocs.io/en/latest/usage.html#using-factory-hooks

    def __init__(self) -> None:
        super().__init__()
        self.register_unstructure_hook(DateTime, self._unstructure_datetime)
        self.register_structure_hook(DateTime, self._structure_datetime)
        self.register_structure_hook(ConfigValue, self._structure_config_value)
        self.register_unstructure_hook_factory(has, self._unstructure_camel_case)
        self.register_structure_hook_factory(has, self._structure_camel_case)

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

    def _unstructure_datetime(self, value: DateTime) -> str:
        """Serialize a DateTime to a string."""
        return value.format(TIMESTAMP_FORMAT)  # type: ignore

    def _structure_datetime(self, value: str, _: Type[DateTime]) -> DateTime:
        """Deserialize input data into a DateTime."""
        return from_format(value, TIMESTAMP_FORMAT, tz=TIMESTAMP_ZONE)

    def _structure_config_value(self, value: Dict[str, Any], _: Type[ConfigValue]) -> ConfigValue:
        """Deserialize input data into a ConfigValue of the proper type."""
        if "valueType" in value and ConfigValueType[value["valueType"]]:
            value_type = ConfigValueType[value["valueType"]]
            return self.structure(value, CONFIG_VALUE_BY_TYPE[value_type])  # type: ignore
        raise ValueError("Unknown config value type")


CONVERTER = LifecycleConverter()


def _phase(d: Dict[str, Any]) -> LifecyclePhase:
    """Determine the phase associated with a request in dict form."""
    if "lifecycle" in d and LifecyclePhase[d["lifecycle"]]:
        return LifecyclePhase[d["lifecycle"]]
    raise ValueError("Could not determine lifecycle phase for request")


def parse_json_request(
    j: str,
) -> LifecycleRequest:
    """Parse a SmartApp lifecycle request request from JSON."""
    d = json.loads(j)
    phase = _phase(d)
    return CONVERTER.structure(d, REQUEST_BY_PHASE[phase])  # type: ignore

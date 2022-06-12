# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Common code for the SmartApp lifecycle.
"""

# See: https://developer-preview.smartthings.com/docs/connected-services/lifecycles/
#      https://developer-preview.smartthings.com/docs/connected-services/configuration/

import json
from abc import ABC
from enum import Enum
from typing import Any, Dict, Type, TypeVar

import yaml
from attrs import fields, frozen, has
from cattrs import GenConverter
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override
from pendulum import from_format
from pendulum.datetime import DateTime

TIMESTAMP_FORMAT = "YYYY-MM-DD[T]HH:mm:ss.SSS[Z]"  # example: "2017-09-13T04:18:12.469Z"
TIMESTAMP_ZONE = "UTC"

T = TypeVar("T")  # pylint: disable=invalid-name
"""Generic type"""


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
        self.register_unstructure_hook(DateTime, lambda d: d.format(TIMESTAMP_FORMAT) if d else None)  # type: ignore
        self.register_structure_hook(DateTime, lambda s, _: from_format(s, TIMESTAMP_FORMAT, tz=TIMESTAMP_ZONE) if s else None)
        self.register_unstructure_hook_factory(has, self._to_camel_case_unstructure)
        self.register_structure_hook_factory(has, self._to_camel_case_structure)

    def to_dict(self, obj: Any) -> Dict[str, Any]:
        """Serialize an object to a dict."""
        return self.unstructure(obj)  # type: ignore

    def from_dict(self, data: Dict[str, Any], cls: Type[T]) -> T:
        """Deserialize an object from a dict."""
        return self.structure(data, cls)

    def to_json(self, obj: Any) -> str:
        """Serialize an object to JSON."""
        return json.dumps(self.to_dict(obj), indent="  ")

    def from_json(self, data: str, cls: Type[T]) -> T:
        """Deserialize an object from JSON."""
        return self.from_dict(json.loads(data), cls)

    def to_yaml(self, obj: Any) -> str:
        """Serialize an object to YAML."""
        return yaml.safe_dump(self.to_dict(obj), sort_keys=False)  # type: ignore

    def from_yaml(self, data: str, cls: Type[T]) -> T:
        """Deserialize an object from YAML."""
        return self.from_dict(yaml.safe_load(data), cls)

    @staticmethod
    def _to_camel_case(snake_str: str) -> str:
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def _to_camel_case_unstructure(self, cls):  # type: ignore
        return make_dict_unstructure_fn(
            cls, self, **{a.name: override(rename=LifecycleConverter._to_camel_case(a.name)) for a in fields(cls)}
        )

    def _to_camel_case_structure(self, cls):  # type: ignore
        return make_dict_structure_fn(
            cls, self, **{a.name: override(rename=LifecycleConverter._to_camel_case(a.name)) for a in fields(cls)}
        )


CONVERTER = LifecycleConverter()


class LifecyclePhase(Enum):
    CONFIRMATION = "CONFIRMATION"
    CONFIGURATION = "CONFIGURATION"
    INSTALL = "INSTALL"
    UPDATE = "UPDATE"
    EVENT = "EVENT"
    OAUTH_CALLBACK = "OAUTH_CALLBACK"
    UNINSTALL = "UNINSTALL"


# TODO: we are going to need some sort of custom structure mechanism for LifecycleRequest,
#       because there's no good way for cattrs to understand how to create the correct
#       subclass.


@frozen
class LifecycleRequest(ABC):
    """Abstract parent class for all types of lifecycle requests."""

    lifecycle: LifecyclePhase
    execution_id: str
    locale: str
    version: str

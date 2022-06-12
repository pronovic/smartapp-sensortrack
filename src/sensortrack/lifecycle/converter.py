# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Converter to serialize and deserialize lifecycle objects to various formats.
"""

import json
from typing import Any, Dict, TypeVar, Union

from attrs import fields, has
from cattrs import GenConverter
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override
from pendulum import from_format
from pendulum.datetime import DateTime

from .interface import (
    ConfigRequest,
    ConfirmationRequest,
    EventRequest,
    InstallRequest,
    LifecyclePhase,
    OauthCallbackRequest,
    UninstallRequest,
    UpdateRequest,
)

TIMESTAMP_FORMAT = "YYYY-MM-DD[T]HH:mm:ss.SSS[Z]"  # example: "2017-09-13T04:18:12.469Z"
TIMESTAMP_ZONE = "UTC"


T = TypeVar("T")  # pylint: disable=invalid-name
"""Generic type"""

REQUEST_BY_PHASE = {
    LifecyclePhase.CONFIGURATION: ConfigRequest,
    LifecyclePhase.CONFIRMATION: ConfirmationRequest,
    LifecyclePhase.INSTALL: InstallRequest,
    LifecyclePhase.UPDATE: UpdateRequest,
    LifecyclePhase.EVENT: EventRequest,
    LifecyclePhase.OAUTH_CALLBACK: OauthCallbackRequest,
    LifecyclePhase.UNINSTALL: UninstallRequest,
}

LifecycleRequest = Union[
    ConfigRequest,
    ConfirmationRequest,
    EventRequest,
    InstallRequest,
    OauthCallbackRequest,
    UninstallRequest,
    UpdateRequest,
]


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

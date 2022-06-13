# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API.
"""
import codecs
import logging
from importlib.metadata import version as metadata_version

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module:

from .dispatcher import DISPATCHER

API_VERSION = "1.0.0"
API = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints


class Health(BaseModel):
    """API health data"""

    status: str = Field("OK")


class Version(BaseModel):
    """API version data"""

    package: str = Field(...)
    api: str = Field(...)


@API.on_event("startup")
async def startup_event() -> None:
    """Do setup at server startup."""
    logging.info("Server startup complete")


@API.on_event("shutdown")
async def shutdown_event() -> None:
    """Do cleanup at server shutdown."""
    logging.info("Server shutdown complete")


@API.get("/health")
def health() -> Health:
    """Return an API health indicator."""
    return Health()


@API.get("/version")
def version() -> Version:
    """Return the API version, including both the package version and the API version"""
    return Version(package=metadata_version("sensor-track"), api=API.version)


@API.post("/smartapp")
async def smartapp(request: Request) -> Response:
    headers = request.headers
    body = await request.body()
    request_json = codecs.decode(body, "UTF-8")
    status, response_json = DISPATCHER.dispatch(headers=headers, request_json=request_json)
    return Response(content=response_json, status_code=status, media_type="application/json")

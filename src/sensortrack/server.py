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

from smartapp.dispatcher import SmartAppRequestContext
from smartapp.interface import BadRequestError, SignatureError, SmartAppError

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


@API.exception_handler(BadRequestError)
async def bad_request_handler(_: Request, e: BadRequestError) -> Response:
    logging.error("[%s] Bad request: %s", e.correlation_id, e)
    return Response(status_code=400)


@API.exception_handler(SignatureError)
async def signature_error_handler(_: Request, e: SignatureError) -> Response:
    logging.error("[%s] Signature error: %s", e.correlation_id, e)
    return Response(status_code=401)


@API.exception_handler(SmartAppError)
async def internal_error_handler(_: Request, e: SmartAppError) -> Response:
    logging.error("[%s] Internal error: %s", e.correlation_id, e)
    return Response(status_code=500)


@API.exception_handler(Exception)
async def exception_handler(_: Request, e: Exception) -> Response:
    logging.error("Internal error: %s", e)
    return Response(status_code=500)


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
    context = SmartAppRequestContext(headers=headers, request_json=request_json)
    response_json = DISPATCHER.dispatch(context=context)
    return Response(status_code=200, content=response_json, media_type="application/json")

# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API.
"""
import codecs
import logging
from importlib.metadata import version as metadata_version

from fastapi import FastAPI, Request, Response
from influxdb_client.client.exceptions import InfluxDBError
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module:
from smartapp.interface import BadRequestError, SignatureError, SmartAppError, SmartAppRequestContext

from sensortrack.dispatcher import dispatcher
from sensortrack.rest import RestClientError

API_VERSION = "1.0.0"
API = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints


class Health(BaseModel):
    """API health data"""

    status: str = Field("OK")


class Version(BaseModel):
    """API version data"""

    package: str = Field(...)
    api: str = Field(...)


def _generic_error_handler(e: Exception, status_code: int, message: str) -> Response:
    """Generic error handle that properly logs the entire exception context."""
    try:
        raise e
    except:  # pylint: disable=bare-except:
        logging.exception(message)
    return Response(status_code=status_code)


@API.exception_handler(BadRequestError)
async def bad_request_handler(_: Request, e: BadRequestError) -> Response:
    return _generic_error_handler(e, 400, "[%s] Bad request: %s" % (e.correlation_id, e))


@API.exception_handler(SignatureError)
async def signature_error_handler(_: Request, e: SignatureError) -> Response:
    return _generic_error_handler(e, 401, "[%s] Signature error: %s" % (e.correlation_id, e))


@API.exception_handler(SmartAppError)
async def smartapp_error_handler(_: Request, e: SmartAppError) -> Response:
    return _generic_error_handler(e, 500, "[%s] SmartApp error: %s" % (e.correlation_id, e))


@API.exception_handler(RestClientError)
async def rest_client_error_handler(_: Request, e: RestClientError) -> Response:
    return _generic_error_handler(e, 500, "%s" % e)


@API.exception_handler(InfluxDBError)
async def influxdb_error_handler(_: Request, e: SmartAppError) -> Response:
    return _generic_error_handler(e, 500, "InfluxDB error: %s" % e)


@API.exception_handler(Exception)
async def exception_handler(_: Request, e: Exception) -> Response:
    return _generic_error_handler(e, 500, "Internal error: %s" % e)


@API.on_event("startup")
async def startup_event() -> None:
    """Do setup at server startup."""
    logging.info("Server startup complete")


@API.on_event("shutdown")
async def shutdown_event() -> None:
    """Do cleanup at server shutdown."""
    logging.info("Server shutdown complete")


@API.get("/health")
async def health() -> Health:
    """Return an API health indicator."""
    return Health()


@API.get("/version")
async def version() -> Version:
    """Return the API version, including both the package version and the API version"""
    return Version(package=metadata_version("sensor-track"), api=API.version)


@API.post("/smartapp")
async def smartapp(request: Request) -> Response:
    """Handle the SmartApp lifecycle requests via the dispatcher implementation."""
    headers = request.headers
    body = codecs.decode(await request.body(), "UTF-8")
    context = SmartAppRequestContext(headers=headers, body=body)
    content = dispatcher().dispatch(context=context)
    return Response(status_code=200, content=content, media_type="application/json")

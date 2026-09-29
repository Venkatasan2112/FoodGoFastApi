import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    NotFoundException,
    ServiceUnavailableException,
    ValidationException,
)

logger = logging.getLogger(__name__)


async def authentication_exception_handler(
    request: Request, exc: AuthenticationException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
    )


async def authorization_exception_handler(
    request: Request, exc: AuthorizationException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.detail},
    )


async def not_found_exception_handler(
    request: Request, exc: NotFoundException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


async def conflict_exception_handler(
    request: Request, exc: ConflictException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(
    request: Request, exc: ValidationException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.detail},
    )


async def service_unavailable_exception_handler(
    request: Request, exc: ServiceUnavailableException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": exc.detail},
    )


async def unexpected_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(f"Unexpected internal server error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

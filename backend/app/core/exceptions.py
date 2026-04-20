from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional
import logging
import uuid


logger = logging.getLogger(__name__)


class RoxyException(Exception):
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(RoxyException):
    pass


class RateLimitError(RoxyException):
    pass


class ProviderError(RoxyException):
    pass


class TaskError(RoxyException):
    pass


class ValidationError(RoxyException):
    pass


class CreditError(RoxyException):
    pass


class ContentPolicyError(RoxyException):
    pass


class StorageError(RoxyException):
    pass


def http_error_from_exception(exc: RoxyException) -> HTTPException:
    error_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        ProviderError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        CreditError: status.HTTP_402_PAYMENT_REQUIRED,
        ContentPolicyError: status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
        StorageError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = error_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=status_code,
        detail={"message": exc.message, "code": exc.code, "details": exc.details}
    )


def get_request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])


async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = get_request_id(request)
    
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} error [{request_id}]: {exc.detail}")
    else:
        logger.warning(f"HTTP {exc.status_code} error [{request_id}]: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id
        },
        headers={"X-Request-ID": request_id}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = get_request_id(request)
    errors = exc.errors()
    
    logger.warning(f"Validation error [{request_id}]: {errors}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": errors,
            "request_id": request_id
        },
        headers={"X-Request-ID": request_id}
    )


async def generic_exception_handler(request: Request, exc: Exception):
    request_id = get_request_id(request)
    
    logger.exception(f"Unhandled exception [{request_id}]: {exc}")
    
    from app.core.config import get_settings
    settings = get_settings()
    
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
                "support": "Please contact support with this request ID"
            },
            headers={"X-Request-ID": request_id}
        )
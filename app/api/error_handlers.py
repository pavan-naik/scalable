from datetime import datetime, timezone

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException, ValidationException, ResourceNotFoundException
from app.core.error_codes import ErrorCode

# Map exception types to HTTP status codes
EXCEPTION_STATUS_MAP = {
    ValidationException: status.HTTP_400_BAD_REQUEST,
    ResourceNotFoundException: status.HTTP_404_NOT_FOUND,
}


async def app_exception_handler(request: Request, exc: AppException):
    """Central exception handler"""
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )


async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Converts FastAPI's RequestValidationError to our standard error format.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": ErrorCode.VAL_REQUEST_INVALID,
                "message": "Request validation failed",
                "details": {"validation_errors": errors},
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.

    Logs full error details but returns generic message to user.
    """
    # logger.exception(
    #     "Unexpected error occurred",
    #     extra={
    #         "path": request.url.path,
    #         "method": request.method,
    #         "error_type": type(exc).__name__,
    #         "error_message": str(exc)
    #     }
    # )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": ErrorCode.SYS_INTERNAL_ERROR,
                "message": "An internal error occurred. Please try again later.",
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )
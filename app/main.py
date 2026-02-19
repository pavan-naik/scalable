from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.routers import health, ml
from app.api.error_handlers import app_exception_handler, validation_exception_handler, generic_exception_handler
from app.core.exceptions import AppException
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=settings.DOCS_URL
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ml.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
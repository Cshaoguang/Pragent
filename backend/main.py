from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.router import api_router
from backend.api.responses import ApiResponse
from backend.config.database import close_database, init_database
from backend.config.logging import configure_logging
from backend.config.redis import close_redis, init_redis
from backend.config.settings import get_settings
from backend.vectorstore.qdrant_store import close_qdrant, init_qdrant


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    await init_database()
    await init_redis()
    await init_qdrant()
    try:
        yield
    finally:
        await close_qdrant()
        await close_redis()
        await close_database()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_prefix)


@app.exception_handler(ValueError)
async def handle_value_error(_: Request, exc: ValueError):
    return JSONResponse(status_code=200, content=ApiResponse(code="1", message=str(exc), data=None).model_dump())


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError):
    message = exc.errors()[0].get("msg", "请求参数错误") if exc.errors() else "请求参数错误"
    return JSONResponse(status_code=200, content=ApiResponse(code="1", message=message, data=None).model_dump())


@app.exception_handler(RuntimeError)
async def handle_runtime_error(_: Request, exc: RuntimeError):
    return JSONResponse(status_code=200, content=ApiResponse(code="1", message=str(exc), data=None).model_dump())


@app.exception_handler(Exception)
async def handle_unknown_error(_: Request, exc: Exception):
    return JSONResponse(status_code=200, content=ApiResponse(code="1", message=str(exc), data=None).model_dump())


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}

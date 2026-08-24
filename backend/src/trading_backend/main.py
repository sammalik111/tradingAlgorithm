import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from trading_backend.api.router import api_router
from trading_backend.config import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Trading Recommendation Platform API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")

    # Starlette's own default 500 handler runs in ServerErrorMiddleware,
    # which wraps CORSMiddleware from the outside -- so an unhandled
    # exception's response never gets CORS headers, and the browser reports
    # an opaque network/CORS failure instead of a readable 500. Registering
    # a handler here runs it in ExceptionMiddleware instead, which sits
    # inside CORSMiddleware, so the response passes through normally.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()

# Entrypoint for API Gateway (HTTP API) -> Lambda, see infra/modules/lambda.
handler = Mangum(app)

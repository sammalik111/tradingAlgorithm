from fastapi import APIRouter

from trading_backend.api.routes import health, politicians, recommendations, trades

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(politicians.router)
api_router.include_router(trades.router)
api_router.include_router(recommendations.router)

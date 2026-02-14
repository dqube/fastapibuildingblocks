"""API v1 router."""

from fastapi import APIRouter

from .endpoints import users, messages, redis, external_api

api_router = APIRouter()

# Include routers
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
api_router.include_router(external_api.router, prefix="/external-api", tags=["external-api"])

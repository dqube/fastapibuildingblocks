"""API v1 router."""

from fastapi import APIRouter

from .endpoints import users

api_router = APIRouter()

# Include routers
api_router.include_router(users.router, prefix="/users", tags=["users"])

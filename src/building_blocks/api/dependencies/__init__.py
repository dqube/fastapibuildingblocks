"""FastAPI dependency injection utilities."""

from .base import Dependency
from .mediator import get_mediator, MediatorDep

__all__ = ["Dependency", "get_mediator", "MediatorDep"]

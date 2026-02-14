"""Base DomainService class for domain services."""

from abc import ABC


class DomainService(ABC):
    """
    Base class for domain services.
    
    Domain services contain business logic that doesn't naturally fit within
    an entity or value object. They operate on multiple domain objects and
    coordinate business operations.
    """
    
    pass

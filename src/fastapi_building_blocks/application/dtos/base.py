"""Base DTO (Data Transfer Object) class."""

from pydantic import BaseModel


class DTO(BaseModel):
    """
    Base class for Data Transfer Objects (DTOs).
    
    DTOs are simple objects used to transfer data between layers.
    They have no business logic and are used to decouple the API layer
    from the domain layer.
    """
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        arbitrary_types_allowed = True
        populate_by_name = True

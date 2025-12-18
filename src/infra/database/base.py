"""SQLAlchemy declarative base for all ORM models."""

from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """
    Base class for all SQLAlchemy ORM models.
    
    Automatically generates __tablename__ from the class name (lowercase).
    All models should inherit from this class.
    
    Example:
        >>> class Tender(Base):
        ...     __tablename__ = "tenders"  # Optional, auto-generated if omitted
        ...     id = Column(Integer, primary_key=True)
    """
    
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name (lowercase)."""
        return cls.__name__.lower()

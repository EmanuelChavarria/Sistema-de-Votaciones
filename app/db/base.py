"""Base declarativa común a todos los modelos."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa de SQLAlchemy 2.0."""

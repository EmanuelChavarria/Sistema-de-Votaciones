"""Modelos ORM de la aplicación."""

from app.models.candidate import Candidate
from app.models.user import User
from app.models.vote import Vote
from app.models.voter import Voter

__all__ = ["Candidate", "User", "Vote", "Voter"]

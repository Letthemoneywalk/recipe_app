from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from db.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ingredients: Mapped[list] = mapped_column(JSON)
    searched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
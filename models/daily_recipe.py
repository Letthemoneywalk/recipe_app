from sqlalchemy import Integer, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime

from db.database import Base


class DailyRecipe(Base):
    __tablename__ = "daily_recipe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(Integer)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
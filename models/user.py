from sqlalchemy import String, Integer, Float, Enum, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from db.database import Base
from core.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    NAME_MAX_LENGTH,
)


class UserDiet(str, enum.Enum):
    regular = "regular"
    vegetarian = "vegetarian"
    vegan = "vegan"
    lactose_free = "lactose_free"
    gluten_free = "gluten_free"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(PASSWORD_MAX_LENGTH))
    name: Mapped[str | None] = mapped_column(String(NAME_MAX_LENGTH))
    age: Mapped[int | None] = mapped_column(Integer)
    weight: Mapped[float | None] = mapped_column(Float)
    height: Mapped[float | None] = mapped_column(Float)
    diet: Mapped[UserDiet] = mapped_column(Enum(UserDiet), default=UserDiet.regular)
    allergens: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    recipes: Mapped[list["Recipe"]] = relationship(back_populates="user")
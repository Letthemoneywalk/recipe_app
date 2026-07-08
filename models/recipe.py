from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from db.database import Base
from core.constants import (
    RECIPE_TITLE_MAX_LENGTH,
    IMAGE_URL_MAX_LENGTH,
)


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Ссылка на Spoonacular
    spoonacular_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(RECIPE_TITLE_MAX_LENGTH))
    image_url: Mapped[str | None] = mapped_column(String(IMAGE_URL_MAX_LENGTH))

    # Оригинальный рецепт
    original_ingredients: Mapped[list] = mapped_column(JSON)
    original_steps: Mapped[list] = mapped_column(JSON)
    original_nutrition: Mapped[dict | None] = mapped_column(JSON)

    # Модифицированный рецепт
    modified_ingredients: Mapped[list] = mapped_column(JSON)
    modified_steps: Mapped[list] = mapped_column(JSON)
    modified_nutrition: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="recipes")
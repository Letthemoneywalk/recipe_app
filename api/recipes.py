import re
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, String
from datetime import date
import json as json_lib

from db.database import get_db
from models.recipe import Recipe
from models.user import User
from core.security import get_current_user
from services.spoonacular import search_recipes_by_ingredients, get_recipe_details, get_random_recipe, autocomplete_ingredient
from schemas.recipe import RecipeSearchResult, RecipeDetail, IngredientSchema, ScaleRequest, ScaleResponse, SubstituteRequest, SubstituteResponse, RecipeFullDTO
from services.claude import substitute_ingredient
from models.search_history import SearchHistory
from models.daily_recipe import DailyRecipe
from core.limiter import limiter

router = APIRouter(prefix="/recipes", tags=["recipes"])


def pretty_round(value: float) -> float:
    if value <= 0:
        return 0
    if value < 5:
        return round(value, 1)    # 1.3, 2.5
    if value < 20:
        return round(value)       # 12, 17
    if value < 100:
        return round(value / 5) * 5    # 25, 30, 35
    return round(value / 10) * 10      # 100, 110, 230


def round_spoons(value: float) -> float:
    return round(value * 2) / 2


def strip_html(text: str | None) -> str | None:
    if not text:
        return None
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


def get_badges(data: dict, nutrition: dict) -> list[str]:
    badges = []
    
    if data.get("vegan"):
        badges.append("Vegan")
    elif data.get("vegetarian"):
        badges.append("Vegetarian")
    
    if data.get("glutenFree"):
        badges.append("Gluten Free")
    
    if data.get("dairyFree"):
        badges.append("Dairy Free")
    
    protein = nutrition.get("protein", 0) or 0
    calories = nutrition.get("calories", 0) or 0
    carbs = nutrition.get("carbs", 0) or 0
    
    if protein > 30:
        badges.append("High Protein")
    
    if carbs < 20:
        badges.append("Low Carb")
    
    ready = data.get("readyInMinutes", 60)
    if ready <= 10:
        badges.append("Under 10 min")
    elif ready <= 20:
        badges.append("Under 20 min")
    
    # Возвращаем максимум 2 бейджа
    return badges[:2]


def parse_ingredients(ingredients_str: str) -> tuple[list[str], dict[str, float], dict[str, int]]:
    names = []
    grams = {}
    pieces = {}

    for item in ingredients_str.split(","):
        item = item.strip()
        match_g = re.match(r"^(.+?)\s+(\d+(?:\.\d+)?)\s*g$", item)
        match_p = re.match(r"^(.+?)\s+(\d+)$", item)

        if match_g:
            name = match_g.group(1).strip()
            names.append(name)
            grams[name] = float(match_g.group(2))
        elif match_p:
            name = match_p.group(1).strip()
            names.append(name)
            pieces[name] = int(match_p.group(2))
        else:
            names.append(item)

    return names, grams, pieces


def build_recipe_dto(data: dict, ratio: float = 1.0) -> RecipeFullDTO:
    import math

    JUNK_STARTS = ("add ", "put", "stir", "if ", "mix", "sprinkle", "in a")
    raw_ingredients = [
        i for i in data.get("extendedIngredients", [])
        if i.get("unit") not in ("servings", "serving")
        and len(i["name"]) < 40
        and not any(i["name"].lower().startswith(j) for j in JUNK_STARTS)
    ]

    ingredients_full = []
    for i in raw_ingredients:
        unit = i["measures"]["metric"]["unitShort"]
        orig_amount = i["amount"] * ratio
        if unit in ("", None):
            ingredients_full.append(f"{i['name']}: {math.ceil(orig_amount)} pcs")
        elif unit in ("cloves", "medium", "large", "small", "whole", "stalks", "piece", "pieces"):
            ingredients_full.append(f"{i['name']}: {math.ceil(orig_amount)} {unit}")
        elif unit in ("Tbsp", "Tbsps", "tsp", "tsps"):
            ingredients_full.append(f"{i['name']}: {round_spoons(orig_amount)} {unit}")
        elif unit in ("l", "L"):
            ingredients_full.append(f"{i['name']}: {pretty_round(i['measures']['metric']['amount'] * ratio * 1000)}ml")
        else:
            ingredients_full.append(f"{i['name']}: {pretty_round(i['measures']['metric']['amount'] * ratio)}{unit}")

    steps = []
    for instruction in data.get("analyzedInstructions", []):
        for step in instruction.get("steps", []):
            steps.append(step["step"])

    raw_nutrition = data.get("nutrition", {})
    nutrients = {n["name"]: n["amount"] for n in raw_nutrition.get("nutrients", [])}
    nutrition = {
        "calories": pretty_round(nutrients.get("Calories", 0) * ratio),
        "protein": pretty_round(nutrients.get("Protein", 0) * ratio),
        "fat": pretty_round(nutrients.get("Fat", 0) * ratio),
        "carbs": pretty_round(nutrients.get("Carbohydrates", 0) * ratio),
    }

    ready = data.get("readyInMinutes", 60)
    if ready <= 20:
        difficulty = "easy"
    elif ready <= 45:
        difficulty = "medium"
    else:
        difficulty = "hard"

    return RecipeFullDTO(
        id=data["id"],
        title=data["title"],
        description=strip_html(data.get("summary")),
        image_url=data.get("image"),
        cook_time=f"{ready} min" if ready else None,
        difficulty=difficulty,
        ingredients_full=ingredients_full,
        steps=steps,
        badges=get_badges(data, nutrition),
        nutrition=nutrition,
        vegetarian=data.get("vegetarian", False),
        vegan=data.get("vegan", False),
        gluten_free=data.get("glutenFree", False),
        dairy_free=data.get("dairyFree", False),
    )


@router.get("/search", response_model=list[RecipeFullDTO])
@limiter.limit("3/minute")
async def search_recipes(
    request: Request,
    ingredients: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import asyncio

    if not ingredients or not ingredients.strip():
        raise HTTPException(status_code=400, detail="Введите хотя бы один ингредиент")

    ingredient_names, user_amounts, user_pieces = parse_ingredients(ingredients)

    if not ingredient_names:
        raise HTTPException(status_code=400, detail="Введите хотя бы один ингредиент")

    # Исправляем названия ингредиентов через autocomplete
    ingredient_names = await asyncio.gather(*[
        autocomplete_ingredient(name) for name in ingredient_names
    ])
    ingredient_names = list(ingredient_names)

    excluded = []
    if current_user.allergens:
        excluded += [a.lower() for a in current_user.allergens]

    results = await search_recipes_by_ingredients(ingredient_names, number=10)

    filtered = []
    for r in results:
        missed = [i["name"].lower() for i in r.get("missedIngredients", [])]
        used = [i["name"].lower() for i in r.get("usedIngredients", [])]
        all_ingredients = missed + used
        has_unwanted = any(
            any(ex in ing for ing in all_ingredients)
            for ex in excluded
        )
        if not has_unwanted:
            filtered.append(r)

    if not filtered:
        raise HTTPException(
            status_code=404,
            detail="Рецепты не найдены. Попробуйте другие ингредиенты."
        )

    top3 = filtered[:3]

    details = await asyncio.gather(*[
        get_recipe_details(r["id"]) for r in top3
    ])

    recipes = []
    for data in details:

        # Считаем ratio если пользователь указал граммовки
        ratio = 1.0
        if user_amounts or user_pieces:
            ratios = []
            raw_ingredients = [
                i for i in data.get("extendedIngredients", [])
                if i.get("unit") not in ("servings", "serving")
                and len(i["name"]) < 40
            ]
            for ing in raw_ingredients:
                ing_name = ing["name"].lower()
                for user_name, user_grams in user_amounts.items():
                    user_words = user_name.lower().split()
                    if any(word == ing_word for ing_word in ing_name.split() for word in user_words):
                        recipe_grams = ing["measures"]["metric"]["amount"]
                        if recipe_grams > 0:
                            ratios.append(user_grams / recipe_grams)
                for user_name, user_count in user_pieces.items():
                    user_words = user_name.lower().split()
                    if any(word == ing_word for ing_word in ing_name.split() for word in user_words):
                        recipe_amount = ing["amount"]
                        if recipe_amount > 0:
                            ratios.append(user_count / recipe_amount)
            if ratios:
                ratio = min(ratios)

                recipes.append(build_recipe_dto(data, ratio))

    # Сохраняем историю поиска — только уникальные запросы
    existing = await db.execute(
        select(SearchHistory).where(
            SearchHistory.user_id == current_user.id,
            SearchHistory.ingredients.cast(String) == json_lib.dumps(ingredient_names),
        )
    )

    history_entry = existing.scalar_one_or_none()

    if history_entry:
        history_entry.searched_at = func.now()
    else:
        db.add(SearchHistory(
            user_id=current_user.id,
            ingredients=ingredient_names,
        ))

    return recipes


@router.get("/saved", response_model=list[RecipeFullDTO])
async def saved_recipes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import asyncio

    result = await db.execute(
        select(Recipe).where(Recipe.user_id == current_user.id)
    )
    saved = result.scalars().all()

    if not saved:
        return []

    details = await asyncio.gather(*[
        get_recipe_details(r.spoonacular_id) for r in saved
    ])

    recipes = []
    for data in details:

        recipes.append(build_recipe_dto(data))

    return recipes


@router.post("/scale", response_model=ScaleResponse)
async def scale_recipe(
    data: ScaleRequest,
    _: User = Depends(get_current_user),
):
    target = next((i for i in data.ingredients if i.id == data.ingredient_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")

    ratio = data.new_amount_grams / target.amount_grams

    scaled = []
    for ingredient in data.ingredients:
        scaled.append(IngredientSchema(
            id=ingredient.id,
            name=ingredient.name,
            amount=pretty_round(ingredient.amount * ratio),
            unit=ingredient.unit,
            amount_grams=pretty_round(ingredient.amount_grams * ratio),
            image_url=ingredient.image_url,
        ))

    nutrition = None
    if data.nutrition:
        nutrition = {
            "calories": pretty_round(data.nutrition["calories"] * ratio),
            "protein": pretty_round(data.nutrition["protein"] * ratio),
            "fat": pretty_round(data.nutrition["fat"] * ratio),
            "carbs": pretty_round(data.nutrition["carbs"] * ratio),
        }

    return ScaleResponse(ingredients=scaled, nutrition=nutrition)

@router.post("/substitute", response_model=SubstituteResponse)
async def substitute(
    data: SubstituteRequest,
    _: User = Depends(get_current_user),
):
    ingredients_dicts = [i.model_dump() for i in data.ingredients]
    
    result = await substitute_ingredient(
        ingredient_name=data.ingredient_name,
        ingredients=ingredients_dicts,
        steps=data.steps,
        nutrition=data.nutrition,
    )

    return SubstituteResponse(
        substitute_name=result["substitute_name"],
        ingredients=[IngredientSchema(**i) for i in result["ingredients"]],
        steps=result["steps"],
        nutrition=result.get("nutrition"),
    )


@router.get("/history")
async def search_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.searched_at.desc())
        .limit(10)
    )
    history = result.scalars().all()
    return [{"ingredients": h.ingredients, "searched_at": h.searched_at} for h in history]


@router.get("/popular-ingredients")
async def popular_ingredients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.searched_at.desc())
        .limit(20)
    )
    history = result.scalars().all()

    # Считаем частоту каждого ингредиента
    counter = {}
    for entry in history:
        for ingredient in entry.ingredients:
            counter[ingredient] = counter.get(ingredient, 0) + 1

    # Сортируем по частоте и берём топ 10
    popular = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"ingredient": name, "count": count} for name, count in popular]


@router.get("/daily", response_model=RecipeFullDTO)
async def daily_recipe(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):

    today = date.today()

    # Проверяем есть ли уже рецепт на сегодня
    result = await db.execute(
        select(DailyRecipe).where(DailyRecipe.date == today)
    )
    daily = result.scalar_one_or_none()

    if daily:
        data = await get_recipe_details(daily.recipe_id)
    else:
        data = await get_random_recipe()
        db.add(DailyRecipe(recipe_id=data["id"], date=today))

    return build_recipe_dto(data)


@router.get("/{spoonacular_id}", response_model=RecipeFullDTO)
async def get_recipe(
    spoonacular_id: int,
    _: User = Depends(get_current_user),
):

    data = await get_recipe_details(spoonacular_id)

    return build_recipe_dto(data)

@router.post("/{spoonacular_id}/save")
async def save_recipe(
    spoonacular_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipe_data = await get_recipe_details(spoonacular_id)

    recipe = Recipe(
        user_id=current_user.id,
        spoonacular_id=spoonacular_id,
        title=recipe_data["title"],
        image_url=recipe_data.get("image"),
        original_ingredients=recipe_data.get("extendedIngredients", []),
        original_steps=recipe_data.get("analyzedInstructions", []),
        original_nutrition=recipe_data.get("nutrition", {}),
        modified_ingredients=recipe_data.get("extendedIngredients", []),
        modified_steps=recipe_data.get("analyzedInstructions", []),
        modified_nutrition=recipe_data.get("nutrition", {}),
    )
    db.add(recipe)
    await db.flush()
    return recipe


@router.delete("/{recipe_id}/save")
async def unsave_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.user_id == current_user.id)
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    await db.delete(recipe)
    return {"message": "Удалено"}
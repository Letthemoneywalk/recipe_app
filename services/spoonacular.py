import httpx
from fastapi import HTTPException
from core.config import settings

BASE_URL = "https://api.spoonacular.com"


async def search_recipes_by_ingredients(ingredients: list[str], number: int = 100) -> list[dict]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/recipes/findByIngredients",
                params={
                    "ingredients": ",".join(ingredients),
                    "number": number,
                    "ranking": 1,
                    "ignorePantry": True,
                    "apiKey": settings.SPOONACULAR_API_KEY,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Сервис рецептов не отвечает. Попробуйте ещё раз.")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 402:
            raise HTTPException(status_code=503, detail="Превышен лимит запросов. Попробуйте позже.")
        raise HTTPException(status_code=502, detail="Ошибка при получении рецептов. Попробуйте ещё раз.")
    except Exception:
        raise HTTPException(status_code=502, detail="Ошибка при получении рецептов. Попробуйте ещё раз.")


async def get_recipe_details(spoonacular_id: int) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/recipes/{spoonacular_id}/information",
                params={
                    "includeNutrition": True,
                    "apiKey": settings.SPOONACULAR_API_KEY,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Сервис рецептов не отвечает. Попробуйте ещё раз.")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 402:
            raise HTTPException(status_code=503, detail="Превышен лимит запросов. Попробуйте позже.")
        raise HTTPException(status_code=502, detail="Ошибка при получении рецепта. Попробуйте ещё раз.")
    except Exception:
        raise HTTPException(status_code=502, detail="Ошибка при получении рецепта. Попробуйте ещё раз.")


async def get_random_recipe() -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/recipes/random",
                params={
                    "number": 1,
                    "includeNutrition": True,
                    "apiKey": settings.SPOONACULAR_API_KEY,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["recipes"][0]
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Сервис рецептов не отвечает. Попробуйте ещё раз.")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 402:
            raise HTTPException(status_code=503, detail="Превышен лимит запросов. Попробуйте позже.")
        raise HTTPException(status_code=502, detail="Ошибка при получении рецепта дня. Попробуйте ещё раз.")
    except Exception:
        raise HTTPException(status_code=502, detail="Ошибка при получении рецепта дня. Попробуйте ещё раз.")


async def autocomplete_ingredient(query: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/food/ingredients/autocomplete",
                params={
                    "query": query,
                    "number": 1,
                    "apiKey": settings.SPOONACULAR_API_KEY,
                },
                timeout=5.0,
            )
            response.raise_for_status()
            results = response.json()
            if results:
                return results[0]["name"]
    except Exception:
        pass
    return query
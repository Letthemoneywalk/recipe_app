import httpx
from core.config import settings

BASE_URL = "https://api.spoonacular.com"


async def search_recipes_by_ingredients(ingredients: list[str], number: int = 10) -> list[dict]:
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


async def get_recipe_details(spoonacular_id: int) -> dict:
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
    

async def get_random_recipe() -> dict:
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
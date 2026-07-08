import json
import anthropic
from core.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


async def substitute_ingredient(
    ingredient_name: str,
    ingredients: list[dict],
    steps: list[str],
    nutrition: dict | None,
) -> dict:
    prompt = f"""
You are a professional chef. A user wants to substitute an ingredient in a recipe.

Ingredient to replace: {ingredient_name}

Current ingredients:
{json.dumps(ingredients, indent=2)}

Current steps:
{json.dumps(steps, indent=2)}

Current nutrition (per serving):
{json.dumps(nutrition, indent=2)}

Tasks:
1. Suggest the best substitute for "{ingredient_name}"
2. Adjust the amounts of the substitute ingredient
3. Rewrite only the steps that mention "{ingredient_name}" using the substitute
4. Recalculate nutrition based on the substitution

Respond with ONLY valid JSON, no markdown:
{{
    "substitute_name": "name of substitute",
    "ingredients": [
        {{
            "id": 0,
            "name": "ingredient name",
            "amount": 1.0,
            "unit": "unit",
            "amount_grams": 100.0,
            "image_url": null
        }}
    ],
    "steps": ["updated step 1", "updated step 2"],
    "nutrition": {{
        "calories": 400,
        "protein": 30,
        "fat": 10,
        "carbs": 40
    }}
}}
"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```json")[-1].split("```")[0].strip()

    return json.loads(text)
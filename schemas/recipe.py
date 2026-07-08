from pydantic import BaseModel


class IngredientSchema(BaseModel):
    id: int
    name: str
    amount: float
    unit: str
    amount_grams: float | None = None
    image_url: str | None = None


class RecipeSearchResult(BaseModel):
    spoonacular_id: int
    title: str
    image_url: str | None
    used_ingredients: int
    missed_ingredients: int


class RecipeDetail(BaseModel):
    spoonacular_id: int
    title: str
    image_url: str | None
    ready_in_minutes: int
    servings: int
    vegetarian: bool
    vegan: bool
    gluten_free: bool
    dairy_free: bool
    ingredients: list[IngredientSchema]
    steps: list[str]
    nutrition: dict | None

class ScaleRequest(BaseModel):
    ingredient_id: int
    new_amount_grams: float
    original_servings: int
    ingredients: list[IngredientSchema]
    nutrition: dict | None = None

class ScaleResponse(BaseModel):
    ingredients: list[IngredientSchema]
    nutrition: dict | None

class SubstituteRequest(BaseModel):
    ingredient_id: int
    ingredient_name: str
    ingredients: list[IngredientSchema]
    steps: list[str]
    nutrition: dict | None = None

class SubstituteResponse(BaseModel):
    substitute_name: str
    ingredients: list[IngredientSchema]
    steps: list[str]
    nutrition: dict | None

class RecipeFullDTO(BaseModel):
    id: int
    title: str
    description: str | None = None
    image_url: str | None = None
    cook_time: str | None = None
    difficulty: str | None = None
    ingredients_full: list[str]
    steps: list[str]
    nutrition: dict | None = None
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False
    dairy_free: bool = False
    badges: list[str] = []
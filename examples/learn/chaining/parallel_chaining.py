import asyncio

from pydantic import BaseModel

from mirascope.core import openai, prompt_template


@openai.call(model="gpt-4o-mini")
@prompt_template(
    """
    Please identify a chef who is well known for cooking with {ingredient}.
    Respond only with the chef's name.
    """
)
async def chef_selector(ingredient: str): ...


class IngredientsList(BaseModel):
    ingredients: list[str]


@openai.call(model="gpt-4o-mini", response_model=IngredientsList)
@prompt_template(
    """
    Given a base ingredient {ingredient}, return a list of complementary ingredients.
    Make sure to exclude the original ingredient from the list.
    """
)
async def ingredients_identifier(ingredient: str): ...


@openai.call(model="gpt-4o-mini")
@prompt_template(
    """
    SYSTEM:
    Your task is to recommend a recipe. Pretend that you are chef {chef}.

    USER:
    Recommend recipes that use the following ingredients:
    {ingredients}
    """
)
async def recipe_recommender(ingredient: str) -> openai.OpenAIDynamicConfig:
    chef, ingredients = await asyncio.gather(
        chef_selector(ingredient), ingredients_identifier(ingredient)
    )
    return {"computed_fields": {"chef": chef, "ingredients": ingredients}}


async def run():
    response = await recipe_recommender(ingredient="apples")
    print(response.content)


asyncio.run(run())

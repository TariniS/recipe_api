from typing import List

import sqlalchemy
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src import database as db
router = APIRouter()

class Ingredient(BaseModel):
    ingredient_name: str
    core_ingredient: str
    quantity: int
    measurement: str


class Instruction(BaseModel):
    step_order: int
    step_name: str


class RecipeJson(BaseModel):
    recipe_name: str
    total_time: str
    servings: int
    spice_level: int
    cooking_level: int
    recipe_description: str
    ingredients: List[Ingredient]
    instructions: List[Instruction]


@router.post("/recipes/{user_id}/recipe/", tags=["recipes"])
def add_recipe(user_id: int, recipe: RecipeJson):
    """
    This endpoint adds a recipe to Recipe. The recipe is represented
    by a recipe name, total time, servings, spice level, cooking level
    recipe description, ingredients, and instructions. It also takes in a user_id
    which links the recipe to that specific user.

    The endpoint returns the id of the resulting recipe that was created.
    """
    existing_user_query = """ SELECT *
                              FROM users 
                              WHERE users.user_id = :user_id"""
    existing_user = db.conn.execute(sqlalchemy.text(existing_user_query),
                                    {'user_id': user_id})
    last_recipe_id = """ SELECT recipe.recipe_id
                              FROM recipe
                              ORDER BY recipe_id DESC"""
    last_ingredient_id = """ SELECT ingredients.ingredient_id
                              FROM ingredients
                              ORDER BY ingredient_id DESC"""
    last_instruction_id = """ SELECT instructions.instruction_id
                              FROM instructions
                              ORDER BY instruction_id DESC"""
    result = db.conn.execute(sqlalchemy.text(last_recipe_id)).first()
    new_recipe_id = int(result[0]) + 1 if result else 0

    result = db.conn.execute(sqlalchemy.text(last_ingredient_id)).first()
    new_ingredient_id = int(result[0]) + 1 if result else 0

    result = db.conn.execute(sqlalchemy.text(last_instruction_id)).first()
    new_instruction_id = int(result[0]) + 1 if result else 0

    # Error checking
    count = 0
    for row in existing_user:
        count += 1
    if count == 0:
        raise HTTPException(status_code=404, detail="user_id not found."
                                                    " Please create a new user.")
    else:

        ingredient_values = [
            {
                "recipe_id": new_recipe_id,
                "ingredient_id": new_ingredient_id + i,
                "ingredient_name": currentIngredient.ingredient_name,
                "core_ingredient": currentIngredient.core_ingredient,
                "quantity": currentIngredient.quantity,
                "measurement": currentIngredient.measurement,
            }
            for i, currentIngredient in enumerate(recipe.ingredients)
        ]

        instruction_values = [
            {
                "instruction_id": new_instruction_id + i,
                "recipe_id": new_recipe_id,
                "step_order": currentInstruction.step_order,
                "step_name": currentInstruction.step_name,
            }
            for i, currentInstruction in enumerate(recipe.instructions)
        ]

        with db.engine.begin() as conn:
            conn.execute(
                sqlalchemy.insert(db.recipes),
                [
                    {
                        "recipe_id": new_recipe_id,
                        "recipe_name": recipe.recipe_name,
                        "user_id": user_id,
                        "total_time": recipe.total_time,
                        "servings": recipe.servings,
                        "spicelevel": recipe.spice_level,
                        "cookinglevel": recipe.cooking_level,
                        "recipe_description": recipe.recipe_description
                    }
                ]
            )
            conn.execute(sqlalchemy.insert(db.ingredients), ingredient_values)
            conn.execute(sqlalchemy.insert(db.instructions), instruction_values)

    return new_recipe_id
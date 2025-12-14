import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True) 
    db = client.recipe_db
    recipes_collection = db.recipes
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route('/')
def index():
    all_recipes = list(recipes_collection.find().sort("name", 1))
    return render_template('index.html', recipes=all_recipes)

@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        recipe_name = request.form['name']
        instructions = request.form['instructions']
        cook_time = request.form['cook_time']

        ingredient_names = request.form.getlist('ingredient_name')
        quantities = request.form.getlist('quantity')
        units = request.form.getlist('unit')

        ingredients_list = []
        for name, qty, unit in zip(ingredient_names, quantities, units):
            if name.strip():
                ingredients_list.append({
                    "name": name.strip(),
                    "quantity": qty.strip(),
                    "unit": unit.strip()
                })

        recipe_doc = {
            "name": recipe_name,
            "instructions": instructions,
            "cook_time": cook_time,
            "ingredients": ingredients_list
        }

        recipes_collection.insert_one(recipe_doc)
        return redirect(url_for('index'))

    return render_template('add_recipe.html')

# NEW ROUTE: Multiple Delete Feature
@app.route('/delete_recipes', methods=['POST'])
def delete_recipes():
    selected_ids = request.form.getlist('selected_recipes')

    if selected_ids:
        try:
            # Convert string IDs to MongoDB ObjectId objects
            object_ids = [ObjectId(recipe_id) for recipe_id in selected_ids]
            # Delete all documents whose _id is in the list
            recipes_collection.delete_many({"_id": {"$in": object_ids}})
        except Exception:
            # Handle potential invalid ID formats silently
            pass
        
    return redirect(url_for('index'))

@app.route('/recipe/<recipe_id>')
def recipe_detail(recipe_id):
    try:
        recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
        
        if recipe:
            return render_template('recipe_detail.html', recipe=recipe)
        else:
            return "Recipe not found", 404
    except Exception as e:
        return f"Invalid ID format or database error: {e}", 400

if __name__ == '__main__':
    # Using host = "0.0.0.0" and a default port that works for Render deployment
    app.run(debug=True, host = "0.0.0.0", port = os.environ.get('PORT', 5002))
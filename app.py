import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId # To handle MongoDB IDs

# --- 1. Configuration & Setup ---
# Load environment variables (like MONGO_URI) from the .env file
load_dotenv()

app = Flask(__name__)
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB Atlas
try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    db = client.recipe_db  # The database where recipes will be stored
    recipes_collection = db.recipes # The collection for the recipe documents
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # Application should not start if connection fails (in a real scenario)

# --- 2. Routes and Logic ---

# Home Page: Display a list of all recipes
@app.route('/')
def index():
    """Fetches all recipes from MongoDB and displays them."""
    # Find all documents in the collection, sorted by name
    all_recipes = list(recipes_collection.find().sort("name", 1))
    # Render the index.html template, passing the recipe list
    return render_template('index.html', recipes=all_recipes)

# Add Recipe Page: Handles both displaying the form (GET) and submitting data (POST)
@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    """Handles submission of a new recipe, including multiple ingredients."""
    if request.method == 'POST':
        # Get basic recipe info from the form
        recipe_name = request.form['name']
        instructions = request.form['instructions']
        cook_time = request.form['cook_time']

        # Handle Multiple Ingredients (The HW Requirement)
        # request.form.getlist() captures ALL values from inputs with the same name
        ingredient_names = request.form.getlist('ingredient_name')
        quantities = request.form.getlist('quantity')
        units = request.form.getlist('unit')

        ingredients_list = []
        # Combine the lists into a structured array of dictionaries
        for name, qty, unit in zip(ingredient_names, quantities, units):
            # Ensure we only save ingredients that have a name entered
            if name.strip():
                ingredients_list.append({
                    "name": name.strip(),
                    "quantity": qty.strip(),
                    "unit": unit.strip()
                })

        # Construct the final document
        recipe_doc = {
            "name": recipe_name,
            "instructions": instructions,
            "cook_time": cook_time,
            "ingredients": ingredients_list # This is the embedded array of multiple entries
        }

        # Insert the document into MongoDB
        recipes_collection.insert_one(recipe_doc)

        # Redirect back to the home page after saving
        return redirect(url_for('index'))

    # For a GET request, just show the form
    return render_template('add_recipe.html')

# Recipe Detail Page: View a single recipe by its MongoDB ID
@app.route('/recipe/<recipe_id>')
def recipe_detail(recipe_id):
    """Fetches a single recipe document using its ObjectId."""
    try:
        # Convert the string ID from the URL into a MongoDB ObjectId
        recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
        
        if recipe:
            return render_template('recipe_detail.html', recipe=recipe)
        else:
            return "Recipe not found", 404
    except Exception as e:
        # Handles cases where the ID format is invalid
        return f"Invalid ID format or database error: {e}", 400

# --- 3. Run the Application ---
if __name__ == '__main__':
    # Use PORT environment variable for deployment (Render), default to 5000 locally
    app.run(debug=True, host = "0.0.0.0", port = "8080")

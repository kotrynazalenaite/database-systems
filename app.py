from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

# Create a Flask web application instance
app = Flask(__name__)

# Database configuration with your details
db_config = {
    'user': 'root',
    'password': 'Bajorai123',  # Password is empty as requested
    'host': 'localhost',
    'database': 'testdb'
}

# ---
# This function is a helper to connect to the database.
# It's a good practice to centralize your connection logic.
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# ---
# This route displays the form for the user to submit a post.
@app.route('/')
def index():
    # Pass a success message to the template if it exists
    success_message = request.args.get('success')
    return render_template('index.html', success_message=success_message)

# ---
# This route handles the form submission and inserts data into the database.
@app.route('/add_post', methods=['POST'])
def add_post():
    # Get the data from the form
    post_content = request.form['post_content']

    # Get a database connection
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed.", 500

    cursor = conn.cursor()

    try:
        # SQL statement to insert data into the example_table
        sql = "INSERT INTO example_table (post) VALUES (%s)"
        # The data to be inserted
        data = (post_content,)
        
        # Execute the SQL statement
        cursor.execute(sql, data)
        
        # Commit the changes to the database
        conn.commit()

        # Redirect back to the home page with a success message
        return redirect(url_for('index', success='true'))

    except mysql.connector.Error as err:
        print(f"Error inserting data: {err}")
        conn.rollback()  # Roll back the transaction if an error occurs
        return "Failed to insert post.", 500
    finally:
        # Close the cursor and connection to free up resources
        cursor.close()
        conn.close()

# ---
# Run the Flask application in debug mode
if __name__ == '__main__':
    app.run(debug=True)

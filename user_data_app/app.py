from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MySQL configurations
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Bajorai123",
    "database": "testdb"
}

# Helper function to get a database connection
def get_db_connection():
    connection = pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        cursorclass=pymysql.cursors.DictCursor  # fetch results as dicts
    )
    return connection

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']

        if not name or not age:
            flash("Please enter both name and age")
            return redirect(url_for('index'))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO user_data (name, age) VALUES (%s, %s)", (name, age))
        conn.commit()
        cur.close()
        conn.close()

        flash("User added successfully!")
        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/users')
def users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_data")
    data = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('users.html', users=data)

if __name__ == "__main__":
    app.run(debug=True, port=5001)

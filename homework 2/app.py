# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from mysql.connector import errorcode # Import errorcode for specific error checking

app = Flask(__name__)

# ----------------------------------------------------------------------
# DATABASE CONFIGURATION
# **MUST BE REPLACED WITH YOUR ACTUAL MYSQL CREDENTIALS**
# ----------------------------------------------------------------------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Bajorai123', # <-- FIX THIS LINE!
    'database': 'university_db'
}

def create_database_if_not_exists(conn):
    """Checks if the target database exists and creates it if necessary."""
    cursor = conn.cursor()
    try:
        # Try to switch to the target database
        cursor.execute(f"USE {DB_CONFIG['database']}")
        print(f"Database '{DB_CONFIG['database']}' selected.")
        return True
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            # Database does not exist, so create it
            try:
                # We must temporarily drop the 'database' key to connect to the server level
                db_name_to_create = DB_CONFIG['database']
                
                # IMPORTANT: Connect without specifying a database to run CREATE DATABASE
                temp_config = DB_CONFIG.copy()
                del temp_config['database']
                
                temp_conn = mysql.connector.connect(**temp_config)
                temp_cursor = temp_conn.cursor()
                
                print(f"Creating database '{db_name_to_create}'...")
                temp_cursor.execute(f"CREATE DATABASE {db_name_to_create}")
                temp_conn.commit()
                
                temp_cursor.close()
                temp_conn.close()

                # Now that it's created, try using it again on the original connection
                cursor.execute(f"USE {db_name_to_create}")
                print(f"Database '{db_name_to_create}' created and selected successfully.")
                return True
                
            except mysql.connector.Error as e:
                print(f"ERROR creating database: {e}")
                return False
        else:
            print(f"Unexpected MySQL error when checking database: {err}")
            return False
    finally:
        cursor.close()

def get_db_connection():
    """Establishes a connection to the MySQL server."""
    # Temporarily remove the database key to connect to the server level first
    connect_config = DB_CONFIG.copy()
    db_name = connect_config['database']
    del connect_config['database']
    
    try:
        conn = mysql.connector.connect(**connect_config)
        # Manually select or create the database
        if not create_database_if_not_exists(conn):
            conn.close()
            return None # Exit if database setup failed
            
        print("SUCCESS: Database connection established and database selected.")
        return conn
    except mysql.connector.Error as err:
        # This print statement will show the exact "Access denied" error in the terminal
        print(f"FATAL ERROR: Could not connect to MySQL server: {err}") 
        print("-------------------------------------------------------------------")
        print("ACTION REQUIRED: Check your DB_CONFIG password and ensure MySQL server is running.")
        print("-------------------------------------------------------------------")
        return None 

# ----------------------------------------------------------------------
# 1. DDL: Initial Table Setup Function
# ----------------------------------------------------------------------
def setup_database():
    """Creates the necessary tables (TEACHER, STUDENT, COURSE, ENROLLMENT) and inserts initial data."""
    # IMPORTANT: The database is now handled by get_db_connection()
    conn = get_db_connection()
    if not conn:
        return # Exit if connection failed
        
    cursor = conn.cursor()
    
    # DDL Statements (These now run against the 'university_db')
    ddl_statements = [
        # Note: Added IF EXISTS to prevent errors if the tables don't exist yet
        "DROP TABLE IF EXISTS ENROLLMENT",
        "DROP TABLE IF EXISTS COURSE",
        "DROP TABLE IF EXISTS STUDENT",
        "DROP TABLE IF EXISTS TEACHER",
        "CREATE TABLE TEACHER (teacher_number VARCHAR(10) PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE)",
        "CREATE TABLE STUDENT (student_number VARCHAR(10) PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE)",
        "CREATE TABLE COURSE (course_number VARCHAR(10) PRIMARY KEY, course_name VARCHAR(100) NOT NULL, course_location VARCHAR(50), teacher_number VARCHAR(10), FOREIGN KEY (teacher_number) REFERENCES TEACHER(teacher_number))",
        "CREATE TABLE ENROLLMENT (student_number VARCHAR(10) NOT NULL, course_number VARCHAR(10) NOT NULL, PRIMARY KEY (student_number, course_number), FOREIGN KEY (student_number) REFERENCES STUDENT(student_number), FOREIGN KEY (course_number) REFERENCES COURSE(course_number))",
    ]
    
    # Insert Initial Data (CREATE operation part 1)
    insert_statements = [
        # --- 5 Teachers as requested ---
        "INSERT INTO TEACHER (teacher_number, name, email) VALUES ('T501', 'Dr. Smith', 'smith@uni.edu')",
        "INSERT INTO TEACHER (teacher_number, name, email) VALUES ('T502', 'Prof. Chen', 'chen@uni.edu')",
        "INSERT INTO TEACHER (teacher_number, name, email) VALUES ('T503', 'Dr. Patel', 'patel@uni.edu')",
        "INSERT INTO TEACHER (teacher_number, name, email) VALUES ('T504', 'Prof. Garcia', 'garcia@uni.edu')",
        "INSERT INTO TEACHER (teacher_number, name, email) VALUES ('T505', 'Ms. Kowalski', 'kowalski@uni.edu')",
        
        # --- Courses linked to the new teachers ---
        "INSERT INTO COURSE (course_number, course_name, course_location, teacher_number) VALUES ('CS101', 'Intro to Programming', 'LIB 305', 'T501')",
        "INSERT INTO COURSE (course_number, course_name, course_location, teacher_number) VALUES ('ART205', 'Digital Media Design', 'ARTS B02', 'T502')",
        "INSERT INTO COURSE (course_number, course_name, course_location, teacher_number) VALUES ('MATH100', 'Calculus I', 'SCI A11', 'T503')",
        "INSERT INTO COURSE (course_number, course_name, course_location, teacher_number) VALUES ('ENG400', 'Creative Writing', 'HUM C04', 'T504')",
        "INSERT INTO COURSE (course_number, course_name, course_location, teacher_number) VALUES ('HIS210', 'World History', 'HUM C01', 'T505')",
        
        # --- Existing Students and Enrollments ---
        "INSERT INTO STUDENT (student_number, name, email) VALUES ('S1001', 'Alice Johnson', 'ajohnson@uni.edu')",
        "INSERT INTO STUDENT (student_number, name, email) VALUES ('S1002', 'Bob Williams', 'bwilliams@uni.edu')",
        "INSERT INTO ENROLLMENT (student_number, course_number) VALUES ('S1001', 'CS101')",
        "INSERT INTO ENROLLMENT (student_number, course_number) VALUES ('S1001', 'ART205')",
        "INSERT INTO ENROLLMENT (student_number, course_number) VALUES ('S1002', 'CS101')",
    ]

    try:
        print("Running DDL and initial inserts...")
        for statement in ddl_statements:
            cursor.execute(statement)
        for statement in insert_statements:
             cursor.execute(statement)
        conn.commit()
        print("SUCCESS: Database setup and initial data loaded successfully.")
    except mysql.connector.Error as err:
        print(f"ERROR during DDL/Insert: {err}")
    finally:
        cursor.close()
        conn.close()

# Call setup function to ensure tables exist when the app starts
setup_database()

# ----------------------------------------------------------------------
# 2. CRUD: READ and JOIN Functionality (Main Route)
# ----------------------------------------------------------------------
@app.route('/')
def index():
    """READ operation: Displays all students and the courses they are enrolled in, 
       and fetches data needed for enrollment forms."""
    conn = get_db_connection()
    if not conn:
        return "<h1>Database Connection Failed</h1><p>Check the console for errors and verify your MySQL credentials in app.py.</p>"
        
    cursor = conn.cursor(dictionary=True) 

    # SQL JOIN: Joins STUDENT, ENROLLMENT, and COURSE tables
    # Includes StudentEmail and TeacherNumber for the clickable links
    join_query = """
    SELECT
        S.student_number,
        S.name AS StudentName,
        S.email AS StudentEmail,
        C.course_number,
        C.course_name,
        T.name AS TeacherName,
        T.teacher_number AS TeacherNumber
    FROM
        STUDENT S
    LEFT JOIN
        ENROLLMENT E ON S.student_number = E.student_number
    LEFT JOIN
        COURSE C ON E.course_number = C.course_number
    LEFT JOIN
        TEACHER T ON C.teacher_number = T.teacher_number
    ORDER BY S.name, C.course_name
    """
    
    try:
        cursor.execute(join_query)
        enrollments = cursor.fetchall()
        
        # READ: Get all students for the UPDATE dropdown list
        cursor.execute("SELECT student_number, name FROM STUDENT ORDER BY name")
        students = cursor.fetchall()
        
        # READ: Get all courses for the CREATE dropdown list
        cursor.execute("SELECT course_number, course_name FROM COURSE ORDER BY course_name")
        courses = cursor.fetchall()

        # READ: Get all teachers for display in the new section 3
        cursor.execute("SELECT teacher_number, name, email FROM TEACHER ORDER BY teacher_number")
        teachers = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"ERROR during main READ query: {err}")
        enrollments = []
        students = [] 
        courses = []
        teachers = [] 
    finally:
        cursor.close()
        conn.close()
    
    # Render the HTML template with data
    return render_template('index.html', 
        enrollments=enrollments, 
        students=students,
        courses=courses, 
        teachers=teachers
    )

# ----------------------------------------------------------------------
# 3. API Route: Get Teacher Details (Used by AJAX/Fetch in HTML)
# ----------------------------------------------------------------------
@app.route('/get_teacher_details/<teacher_id>')
def get_teacher_details(teacher_id):
    """API endpoint to get teacher details for the modal."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch the teacher's ID, Name (Contact Name), and Email
        cursor.execute("SELECT teacher_number, name, email FROM TEACHER WHERE teacher_number = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if teacher:
            return jsonify(teacher)
        return jsonify({'error': 'Teacher not found'}), 404
    except mysql.connector.Error as err:
        print(f"Error fetching teacher details: {err}")
        return jsonify({'error': 'Database query failed'}), 500
    finally:
        cursor.close()
        conn.close()

# ----------------------------------------------------------------------
# 4. API Route: Get Course Details (Used by AJAX/Fetch in HTML)
# ----------------------------------------------------------------------
@app.route('/get_course_details/<course_id>')
def get_course_details(course_id):
    """API endpoint to get course details (location)."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch the course name and location
        cursor.execute("SELECT course_name, course_location FROM COURSE WHERE course_number = %s", (course_id,))
        course = cursor.fetchone()
        if course:
            return jsonify(course)
        return jsonify({'error': 'Course not found'}), 404
    except mysql.connector.Error as err:
        print(f"Error fetching course details: {err}")
        return jsonify({'error': 'Database query failed'}), 500
    finally:
        cursor.close()
        conn.close()


# ----------------------------------------------------------------------
# 5. CRUD: CREATE Operation (Add Student and Enroll)
# ----------------------------------------------------------------------
@app.route('/add_enrollment', methods=['POST'])
def add_enrollment():
    """CREATE operation: Adds a new student record and enrolls them in a selected course."""
    student_num = request.form['student_number']
    name = request.form['name']
    email = request.form['email']
    course_num = request.form['course_number']
    
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    try:
        # 1. Insert into STUDENT table
        sql_student = "INSERT INTO STUDENT (student_number, name, email) VALUES (%s, %s, %s)"
        cursor.execute(sql_student, (student_num, name, email))
        
        # 2. Insert into ENROLLMENT table (only if a course was selected)
        if course_num:
            sql_enroll = "INSERT INTO ENROLLMENT (student_number, course_number) VALUES (%s, %s)"
            cursor.execute(sql_enroll, (student_num, course_num))
            
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error during student insert or enrollment: {err}")
        # Rollback the transaction in case of error (e.g., duplicate primary key)
        conn.rollback() 
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('index'))

# ----------------------------------------------------------------------
# 6. CRUD: UPDATE Operation (Update Email)
# ----------------------------------------------------------------------
@app.route('/update_email', methods=['POST'])
def update_email():
    """UPDATE operation: Updates a student's email."""
    student_num = request.form['student_number']
    new_email = request.form['new_email']
    
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE STUDENT SET email = %s WHERE student_number = %s", (new_email, student_num))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error during update: {err}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('index'))

# ----------------------------------------------------------------------
# 7. CRUD: DELETE Operation
# ----------------------------------------------------------------------
@app.route('/delete_student/<student_num>', methods=['POST'])
def delete_student(student_num):
    """DELETE operation: Deletes a student."""
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    try:
        # Important: Delete from ENROLLMENT first due to foreign key constraint
        cursor.execute("DELETE FROM ENROLLMENT WHERE student_number = %s", (student_num,))
        cursor.execute("DELETE FROM STUDENT WHERE student_number = %s", (student_num,))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error during delete: {err}")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

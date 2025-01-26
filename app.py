from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Database connection
def get_db_connection():
    conn = sqlite3.connect('kerala_diet.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database (create tables if they don't exist)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DietPlans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            age INTEGER,
            weight INTEGER,
            height INTEGER,
            health_condition TEXT,
            diet_preference TEXT,
            include_foods TEXT,
            avoid_foods TEXT,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Register a new user
def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute('INSERT INTO Users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()

# Authenticate a user
def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, password FROM Users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return user['id']  # Return user ID if authentication is successful
    return None  # Authentication failed

# Save a diet plan to the database
def save_diet_plan(user_id, age, weight, height, health_condition, diet_preference, include_foods, avoid_foods):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO DietPlans (user_id, age, weight, height, health_condition, diet_preference, include_foods, avoid_foods)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, age, weight, height, health_condition, diet_preference, include_foods, avoid_foods))
    conn.commit()
    conn.close()

# Fetch diet plans for a user
def get_diet_plans(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM DietPlans WHERE user_id = ?', (user_id,))
    diet_plans = cursor.fetchall()
    conn.close()
    return diet_plans

# Initialize the database when the app starts
init_db()

# Route to serve the home page
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))  # Redirect to login if not logged in
    return render_template('index.html')

# Route to serve the login page
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# Route to handle login form submission
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    user_id = login_user(username, password)
    if user_id:
        session['user_id'] = user_id  # Store user ID in session
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid username or password"})

# Route to serve the registration page
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# Route to handle registration form submission
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']

    if register_user(username, password):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Username already exists"})

# Route to handle diet plan form submission
@app.route('/get-diet-plan', methods=['POST'])
def diet_plan():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not logged in"})

    data = request.json
    age = data['age']
    weight = data['weight']
    height = data['height']
    health_condition = data['healthCondition']
    diet_preference = data['dietPreference']

    # Generate diet plan
    include_foods = ["brown rice", "vegetables", "fruits", "lean protein"]
    avoid_foods = ["processed foods", "sugary drinks", "excess oil"]

    if diet_preference == "vegetarian":
        include_foods.extend(["sambar", "avial", "thoran"])
    else:
        include_foods.extend(["fish curry", "chicken stew"])

    if health_condition == "diabetes":
        avoid_foods.extend(["white rice", "sweets"])
    elif health_condition == "hypertension":
        avoid_foods.extend(["pickles", "excess salt"])
    elif health_condition == "cholesterol":
        avoid_foods.extend(["fried foods", "red meat"])

    # Save diet plan to database
    user_id = session['user_id']
    save_diet_plan(user_id, age, weight, height, health_condition, diet_preference, ', '.join(include_foods), ', '.join(avoid_foods))

    return jsonify({
        "include": include_foods,
        "avoid": avoid_foods,
        "calorie_info": "A typical Kerala meal should ideally contain around 500-700 calories."
    })

# Route to fetch diet plans for the logged-in user
@app.route('/my-diet-plans', methods=['GET'])
def my_diet_plans():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not logged in"})

    user_id = session['user_id']
    diet_plans = get_diet_plans(user_id)

    # Convert diet plans to a list of dictionaries
    plans = []
    for plan in diet_plans:
        plans.append({
            "age": plan['age'],
            "weight": plan['weight'],
            "height": plan['height'],
            "health_condition": plan['health_condition'],
            "diet_preference": plan['diet_preference'],
            "include_foods": plan['include_foods'].split(', '),
            "avoid_foods": plan['avoid_foods'].split(', ')
        })

    return jsonify({"success": True, "diet_plans": plans})

# Route to handle logout
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('kerala_diet.db', check_same_thread=False)
cursor = conn.cursor()

# Create Users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Create DietPlans table (optional)
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

# Function to register a new user
def register_user(username, password):
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute('INSERT INTO Users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists

# Function to check user credentials
def login_user(username, password):
    cursor.execute('SELECT password FROM Users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user and check_password_hash(user[0], password):
        return True
    return False

# Function to save a diet plan
def save_diet_plan(user_id, age, weight, height, health_condition, diet_preference, include_foods, avoid_foods):
    cursor.execute('''
    INSERT INTO DietPlans (user_id, age, weight, height, health_condition, diet_preference, include_foods, avoid_foods)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, age, weight, height, health_condition, diet_preference, include_foods, avoid_foods))
    conn.commit()

# Function to fetch a user's diet plans
def get_diet_plans(user_id):
    cursor.execute('SELECT * FROM DietPlans WHERE user_id = ?', (user_id,))
    return cursor.fetchall()
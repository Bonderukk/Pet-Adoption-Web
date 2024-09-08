from flask import Flask, render_template, request, redirect, url_for
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import sqlite3
import os

app = Flask(__name__)


# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('pets.db')
    conn.row_factory = sqlite3.Row
    return conn


# Initialize the database and create the table if it doesn't exist
def init_db():
    if not os.path.exists('pets.db'):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                breed TEXT NOT NULL,
                age INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
        ''')
        connection.commit()
        connection.close()


# Insert a sample pet into the database
def insert_sample_pet():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if the sample pet is already in the database
    cursor.execute("SELECT * FROM pets WHERE name = 'Buddy'")
    result = cursor.fetchone()

    if not result:
        cursor.execute('''
            INSERT INTO pets (name, breed, age, latitude, longitude)
            VALUES ('Buddy', 'Golden Retriever', 3, 48.1486, 17.1077)  -- Bratislava coordinates
        ''')
        connection.commit()

    connection.close()


# Home route
@app.route('/')
def index():
    return render_template('index.html')


# Search route
@app.route('/search', methods=['GET'])
def search():
    location = request.args.get('location')

    if location:
        # Geocode the user input location to get coordinates
        geolocator = Nominatim(user_agent="pet_adoption_sk")
        user_location = geolocator.geocode(location)

        if user_location:
            user_coords = (user_location.latitude, user_location.longitude)

            # Fetch pets and their locations from the database
            conn = get_db_connection()
            pets = conn.execute('SELECT * FROM pets').fetchall()
            conn.close()

            # Filter pets within 50 km radius
            pets_within_radius = []
            for pet in pets:
                pet_coords = (pet['latitude'], pet['longitude'])
                distance = geodesic(user_coords, pet_coords).km

                if distance <= 50:  # 50 km radius
                    pets_within_radius.append(pet)

            return render_template('results.html', pets=pets_within_radius, location=location)

    return render_template('index.html', location=location)


# Adoption route
@app.route('/adopt', methods=['GET'])
def adopt():
    category = request.args.get('category', 'all')  # Default to 'all' if no category is specified
    return render_template('adopt.html', category=category)


# Contact route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Process contact form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        return redirect(url_for('index'))
    return render_template('contact.html')


if __name__ == '__main__':
    # Initialize the database and insert a sample pet
    init_db()
    insert_sample_pet()

    # Run the Flask app
    app.run(debug=True)

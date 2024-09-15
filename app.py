from flask import Flask, render_template, request, redirect, url_for
from geopy import location
from geopy.distance import geodesic
import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for
from geopy.geocoders import Nominatim
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Slovak city coordinates (latitude and longitude)
city_coordinates = {
    'Bratislava': (48.1486, 17.1077),
    'Košice': (48.7164, 21.2611),
    'Prešov': (48.9985, 21.2336),
    'Žilina': (49.2234, 18.7394),
    'Nitra': (48.3069, 18.0854),
    'Trnava': (48.3774, 17.5883),
    'Trenčín': (48.8945, 18.0444),
    'Banská Bystrica': (48.7395, 19.1531),
}


def get_db_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the current directory of app.py
    db_path = os.path.join(base_dir, 'pets.db')            # Construct the absolute path to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)



UPLOAD_FOLDER = 'C:/Users/matus/PycharmProjects/AdoptPet/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def get_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename))


import os
from werkzeug.utils import secure_filename

@app.route('/add_pet', methods=['GET', 'POST'])
def add_pet():
    if request.method == 'POST':
        name = request.form['name']
        breed = request.form['breed']
        age = int(request.form['age'])
        category = request.form['category']
        city = request.form['city']

        # Handle the image upload
        if 'pet_image' not in request.files:
            return redirect(request.url)
        file = request.files['pet_image']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"Saving file to {file_path}")  # Debug line
            file.save(file_path)

        # Get city coordinates (assuming valid Slovak cities)
        latitude, longitude = city_coordinates.get(city, (None, None))
        if latitude and longitude:
            # Insert the new pet into the database, including the image filename
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO pets (name, breed, age, category, city, latitude, longitude, image_filename)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, breed, age, category, city, latitude, longitude, filename))
            conn.commit()
            conn.close()

            return redirect(url_for('index'))
        else:
            error_message = f"City '{city}' not found. Please choose from the predefined cities."
            return render_template('add_pet.html', error_message=error_message)

    return render_template('add_pet.html')




def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        breed TEXT NOT NULL,
        age INTEGER NOT NULL,
        category TEXT NOT NULL,
        city TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        image_filename TEXT  -- Store the image filename
    )''')

    conn.commit()
    conn.close()


def insert_sample_pet():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if the sample pet is already in the database
    cursor.execute("SELECT * FROM pets WHERE name = 'Buddy'")
    result = cursor.fetchone()

    if not result:
        cursor.execute('''
            INSERT INTO pets (name, breed, age, category, city, latitude, longitude)
            VALUES ('Buddy', 'Golden Retriever', 3, 'Dog', 'Bratislava', 48.1486, 17.1077)
        ''')
        connection.commit()

    connection.close()


# Home route to display pets
@app.route('/')
def index():
    connection = get_db_connection()
    pets = connection.execute('SELECT * FROM pets').fetchall()
    connection.close()

    return render_template('index.html', pets=pets)


# Search route to find pets within 50 km radius

@app.route('/search', methods=['GET'])
def search():
    location = request.args.get('location')
    category = request.args.get('category')

    if location:
        # Geocode the user input location to get coordinates
        geolocator = Nominatim(user_agent="pet_adoption_sk")
        user_location = geolocator.geocode(location)

        if user_location:
            user_coords = (user_location.latitude, user_location.longitude)

            # Fetch pets and their locations from the database
            conn = get_db_connection()
            query = 'SELECT * FROM pets WHERE category LIKE ?'
            pets = conn.execute(query, ('%' + category + '%',)).fetchall()
            conn.close()

            # Filter pets within 50 km radius
            pets_within_radius = []
            for pet in pets:
                pet_coords = (pet['latitude'], pet['longitude'])
                distance = geodesic(user_coords, pet_coords).km

                if distance <= 50:  # 50 km radius
                    pets_within_radius.append(pet)

            if pets_within_radius:
                return render_template('results.html', pets=pets_within_radius, location=location)
            else:
                return render_template('no_results.html', location=location)

    return render_template('index.html', location=location)

@app.route('/adopt', methods=['GET'])
def adopt():

    category = request.args.get('category', 'all')  # Default to 'all' if no category is specified

    conn = get_db_connection()

    # Fetch pets from the database based on the selected category
    if category == 'all':
        pets = conn.execute('SELECT * FROM pets').fetchall()
    elif category == 'dogs':
        pets = conn.execute("SELECT * FROM pets WHERE category = 'Dog'").fetchall()
    elif category == 'cats':
        pets = conn.execute("SELECT * FROM pets WHERE category = 'Cat'").fetchall()
    elif category == 'other':
        pets = conn.execute("SELECT * FROM pets WHERE category = 'Other'").fetchall()
    elif category == 'shelters':
        pets = conn.execute("SELECT * FROM pets WHERE category = 'Shelter'").fetchall()

    conn.close()

    return render_template('adopt.html', pets=pets, category=category)


# Contact route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Process contact form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Here you could handle form data, e.g., send an email
        return redirect(url_for('index'))
    return render_template('contact.html')



def add_image_data_column():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Add image_data column as a BLOB
    cursor.execute('''
        ALTER TABLE pets ADD COLUMN image_data BLOB
    ''')

    conn.commit()
    conn.close()




if __name__ == '__main__':
    # Initialize the database and insert a sample pet
    init_db()
    #insert_sample_pet()

    # Run the Flask app
    app.run(debug=True)

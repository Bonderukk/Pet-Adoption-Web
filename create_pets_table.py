import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
connection = sqlite3.connect('pets.db')

# Create a cursor object using the connection
cursor = connection.cursor()

# Create the 'pets' table
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

# Commit the changes and close the connection
connection.commit()
connection.close()

print("Database and table created successfully!")

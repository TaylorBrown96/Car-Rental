import sqlite3
import hashlib


# Define database path and dictionaries for vehicle makes and models
db_path = 'car_rental.db'


# Retrieve user data by email from the database
def get_user(email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email=?", (email,))
    data = cursor.fetchone()
    conn.close()
    
    return data

# Retrieve all user IDs and names from the database for dropdowns
def get_all_users():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT UserID, Name FROM Users")
    data = cursor.fetchall()
    conn.close()
    
    return data


# Insert a new user into the database
def create_user(name, address, phone, email, age, gender, password, userType=0):
    # Hash password before storing
    password = hashlib.sha3_512(password.encode()).hexdigest()
    username = email.split("@")[0]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Users (UserID, Name, Address, Phone, Email, Age, Gender, InsuranceCompany, UserPhoto, Username, Password, DLPhotos, Usertype) VALUES (NULL, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL, ?)", (name, address, phone, email, age, gender, username, password, userType, ))
    conn.commit()
    conn.close()


# Retrieve vehicles based on filter criteria
def filter_vehicles(type, make, model, drive, transmission, location):
    # If filter criteria are empty, set them to wildcard for SQL query
    if type == "":
        type = "%"
    if make == "":
        make = "%"
    if model == "":
        model = "%"
    if drive == "":
        drive = "%"
    if transmission == "":
        transmission = "%"
    if location == "":
        location = "%"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicles WHERE Type LIKE ? AND Make LIKE ? AND Model LIKE ? AND DriveTrain LIKE ? AND Transmission LIKE ? AND LocationID LIKE ?", (type, make, model, drive, transmission, location))
    data = cursor.fetchall()
    conn.close()
    
    return data


# Retrieve all vehicle data from the database
def get_vehicle_information():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicles")
    data = cursor.fetchall()
    conn.close()
    
    return data


# Retrieve a specific vehicle by its ID
def get_vehicle_by_id(vehicle_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicles WHERE VehicleID = ?", (vehicle_id,))
    vehicle = cursor.fetchone()
    conn.close()
    return vehicle


# Retrieve location data by location ID
def get_location_by_id(location_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Locations WHERE LocationID = ?", (location_id,))
    location = cursor.fetchone()
    conn.close()
    return location


def get_rates_by_vehicle_type(vehicle_type):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM RentalPlans WHERE Type = ?", (vehicle_type,))
    rates = cursor.fetchall()
    conn.close()
    return rates


def get_reserved_dates(vehicle_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ReserveStartDate, ReserveEndDate FROM Reservations WHERE VehicleID = ?", (vehicle_id,))
    dates = cursor.fetchall()
    conn.close()
    return dates


def insert_customer(customer_data, photo_filename, username, password):
    try:
        # Open a connection to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure you are passing all the values as expected
        cursor.execute('''
            INSERT INTO Users (Name, Address, Phone, Email, Age, Gender, InsuranceCompany, UserPhoto, Username, Password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer_data['name'],              # 1
            customer_data['address'],           # 2
            customer_data['phone'],             # 3
            customer_data['email'],             # 4
            customer_data['age'],               # 5
            customer_data['gender'],            # 6
            customer_data['insurance_company'], # 7
            photo_filename,                     # 8
            username,                           # 9
            password                            # 10
        ))

        # Commit changes and close the connection
        conn.commit()
        conn.close()

    except Exception as e:
        # Handle any exception during the insert process
        print(f"Error inserting customer: {e}")
        raise


def update_customer_in_db(user_id, name, address, phone, email, age, gender, insurance_company, photo_filename):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update the customer details in the database
    cursor.execute('''
        UPDATE Users
        SET Name = ?, Address = ?, Phone = ?, Email = ?, Age = ?, Gender = ?, InsuranceCompany = ?, UserPhoto = ?
        WHERE UserID = ?
    ''', (name, address, phone, email, age, gender, insurance_company, photo_filename, user_id))

    conn.commit()
    conn.close()


def mark_customer_inactive(user_id):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update the Active status to False for the given UserID
    cursor.execute("UPDATE Users SET Active = ? WHERE UserID = ?", ("False", user_id))

    # Commit and close the connection
    conn.commit()
    conn.close()
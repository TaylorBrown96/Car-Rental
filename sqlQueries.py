import sqlite3
import hashlib
from datetime import datetime


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


def filter_vehicles_by_dates(type, make, model, drive, transmission, location, start_date, end_date):
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

    # Query to exclude vehicles with any overlapping reservations explicitly
    query = """
    SELECT V.*
    FROM Vehicles V
    WHERE V.Type LIKE ?
      AND V.Make LIKE ?
      AND V.Model LIKE ?
      AND V.DriveTrain LIKE ?
      AND V.Transmission LIKE ?
      AND V.LocationID LIKE ?
      AND NOT EXISTS (
        SELECT 1
        FROM Reservations R
        WHERE R.VehicleID = V.VehicleID
          AND (
            DATE(substr(R.ReserveStartDate, 7, 4) || '-' || substr(R.ReserveStartDate, 1, 2) || '-' || substr(R.ReserveStartDate, 4, 2)) <= DATE(?)
            AND DATE(substr(R.ReserveEndDate, 7, 4) || '-' || substr(R.ReserveEndDate, 1, 2) || '-' || substr(R.ReserveEndDate, 4, 2)) >= DATE(?)
          )
      )
    """
    
    # Convert the incoming dates to YYYY-MM-DD format for SQL comparison
    formatted_start_date = f"{start_date[6:]}-{start_date[:2]}-{start_date[3:5]}"
    formatted_end_date = f"{end_date[6:]}-{end_date[:2]}-{end_date[3:5]}"
    
    cursor.execute(query, (type, make, model, drive, transmission, location, formatted_end_date, formatted_start_date))
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
   
   
def determine_service_id(mileage):
    mileage = int(mileage)
    if mileage <= 5000:
        return 1
    elif mileage <= 10000:
        return 2
    elif mileage <= 15000:
        return 3
    elif mileage <= 25000:
        return 4
    elif mileage <= 50000:
        return 5
    else:
        return 9
    
    
def insert_vehicle(vehicle_data):
    try:
        serviceid = determine_service_id(vehicle_data['mileage'])
        # Open a connection to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure you are passing all the values as expected
        cursor.execute('''
            INSERT INTO Vehicles (Make, Model, Year, Type, Mileage, Transmission, NumDoors, 
            RepairStatus, Available, Photos, LocationID, ServiceID, KeyFeatures, Description,
            DriveTrain)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vehicle_data['make'],              # 1
            vehicle_data['model'],           # 2
            vehicle_data['year'],             # 3
            vehicle_data['type'],             # 4
            vehicle_data['mileage'],               # 5
            vehicle_data['transmission'],            # 6
            vehicle_data['numdoors'], # 7
            vehicle_data['repairstatus'], # 8
            vehicle_data['available'],
            vehicle_data['photos'], # 11
            vehicle_data['locationid'], # 11
            serviceid, # 12
            vehicle_data['keyfeatures'], # 13
            vehicle_data['description'], # 14
            vehicle_data['drivetrain'] # 15
            
        ))

        # Commit changes and close the connection
        conn.commit()
        conn.close()
        

    except Exception as e:
        # Handle any exception during the insert process
        print(f"Error adding vehicle: {e}")
        raise

# Function to update car availability in the database
def update_car_status(cursor, car_id, availability):
    cursor.execute("UPDATE Vehicles SET Available = ? WHERE VehicleID = ?", (availability, car_id))
   

def pick_up_car(user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if the reservation's PickUpLocation matches the vehicle's LocationID
        cursor.execute("""
            SELECT r.VehicleID, r.PickUpLocation, v.LocationID
            FROM Reservations r
            JOIN Vehicles v ON r.VehicleID = v.VehicleID
            WHERE r.UserID = ? AND r.PickUpLocation = v.LocationID AND v.Available = 'Yes'
            LIMIT 1
        """, (user_id,))
        reservation = cursor.fetchone()

        if reservation:
            vehicle_id, pickup_location, location_id = reservation

            # Update the vehicle's availability
            update_car_status(cursor, vehicle_id, "No")

            # Commit changes
            conn.commit()
            print(f"Vehicle {vehicle_id} picked up from location {pickup_location}")
            return True
        else:
            print(f"No valid reservation found for UserID {user_id} with matching pickup location")
            return False
    finally:
        conn.close()
# Function to check and update mileage of a vehicle for 

# Function to drop off car
def drop_off_car(user_id):
    conn = sqlite3.connect(db_path, timeout=10)  # Add timeout
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT VehicleID, DropOffLocation
            FROM Reservations
            WHERE UserID = ? AND PickUpLocation IS NOT NULL AND DropOffLocation IS NOT NULL
            LIMIT 1
        """, (user_id,))
        reservation = cursor.fetchone()

        print(f"Query Result: {reservation}")  # Debugging output

        if reservation:
            vehicle_id, dropoff_location_id = reservation

            # Update vehicle's location to match drop-off location
            cursor.execute("""
                UPDATE Vehicles
                SET LocationID = ?
                WHERE VehicleID = ?
            """, (dropoff_location_id, vehicle_id))

            print(f"Updated Vehicle LocationID to {dropoff_location_id}")

            # Mark vehicle as available
            update_car_status(cursor, vehicle_id, "Yes")

            # Commit the transaction
            conn.commit()
            print(f"Vehicle {vehicle_id} dropped off successfully at location {dropoff_location_id}.")
            return True
        else:
            print(f"No valid reservation found for UserID {user_id}")
            return False
    finally:
        conn.close()


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
    
def update_vehicle_in_db(vehicle_id, make, model, year, type, mileage, transmission, numdoors, repairstatus, available,  photos, locationid, serviceid, keyfeatures, description, drivetrain):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update the vehicle details in the database
    cursor.execute('''
        UPDATE Vehicles
        SET Make = ?, Model = ?, Year = ?, Type = ?, Mileage = ?, Transmission = ?, NumDoors = ?, 
        RepairStatus = ?, Available = ?, Photos = ?, LocationID = ?, ServiceID = ?, KeyFeatures = ?, 
        Description = ?, DriveTrain = ?
        WHERE VehicleID = ?
    ''', (make, model, year, type, mileage, transmission, numdoors, repairstatus, available, photos, locationid, serviceid, keyfeatures, description, drivetrain, vehicle_id))

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
    

def mark_vehicle_inactive(vehicle_id):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update the Active status to False for the given UserID
    cursor.execute("UPDATE Vehicles SET Active = ? WHERE VehicleID = ?", ("False", vehicle_id))

    # Commit and close the connection
    conn.commit()
    conn.close()
    
    
def make_reservation_db(vehicleid, planid, customerid, startdate, enddate, numdays, location, userID, totalprice):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Reservations (VehicleID, UserID, PlanID, ReserveStartDate, ReserveEndDate, NumDays, PickUpLocation, DropOffLocation, CustomerID, TotalPrice) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (vehicleid, userID, planid, startdate, enddate, numdays, location, location, customerid, totalprice))
    conn.commit()
    conn.close()
    
    return True

def update_reservation_db(ReservationID, InvoiceID):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Reservations SET InvoiceID = ? WHERE ReservationID = ?", (InvoiceID, ReservationID))
    conn.commit()
    conn.close()
    
    return True


def make_invoice_db(planID, ReservationID, VehicleID, CustomerID):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Invoice (PlanID, ReservationID, VehicleID, CustomerID) VALUES (?, ?, ?, ?)", (planID, ReservationID, VehicleID, CustomerID))
    conn.commit()
    conn.close()
    
    return True


def get_invoiceid_by_reservationid(reservationid):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT InvoiceID FROM Invoice WHERE ReservationID = ?", (reservationid,))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None


def insert_customer(name, address, phone, email, filename):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Customers (Name, Address, Phone, Email, DLPhoto) VALUES (?, ?, ?, ?, ?)", (name, address, phone, email, filename))
    conn.commit()
    conn.close()
    

def get_customerid_by_email(email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT CustomerID FROM Customers WHERE Email = ?", (email,))
    data = cursor.fetchone()
    conn.close()
    
    return data


def get_planid_by_vehicleid(vehicleid):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rp.PlanID 
        FROM RentalPlans rp
        JOIN Vehicles v ON rp.Type = v.Type
        WHERE v.VehicleID = ?
    """, (vehicleid,))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None


def get_reservationid_by_customerid(customerid, vehicleid, startdate, enddate):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ReservationID FROM Reservations WHERE CustomerID = ? AND VehicleID = ? AND ReserveStartDate = ? AND ReserveEndDate = ?", (customerid, vehicleid, startdate, enddate))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None


def get_reservation_by_id(reservationid):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Reservations WHERE ReservationID = ?", (reservationid,))
    data = cursor.fetchone()
    conn.close()
    
    return data


def get_reservations_tableData(numRows=5, pickedup=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ReservationID, VehicleID, ReserveStartDate, ReserveEndDate, InvoiceID, CustomerID FROM Reservations WHERE PickedUp = ? ORDER BY ReservationID DESC LIMIT ?", (str(pickedup), numRows,))
    data = cursor.fetchall()
    conn.close()
    
    return data


def get_emailData_by_customerid(customer_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT Email FROM Customers WHERE CustomerID = ?", (customer_id,))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None


def get_payment_status(reservation_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT PaymentStatus FROM Invoice WHERE ReservationID = ?", (reservation_id,))
    data = cursor.fetchone()
    conn.close()
    
    return data[0] if data else None
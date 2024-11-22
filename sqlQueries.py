import sqlite3
import hashlib
from datetime import datetime

# Database configuration
db_path = 'car_rental.db'

# ---------------------- User Management ----------------------

def get_user(email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email=?", (email,))
    data = cursor.fetchone()
    conn.close()
    return data

def get_all_users():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT UserID, Name FROM Users")
    data = cursor.fetchall()
    conn.close()
    return data

def create_user(name, address, phone, email, age, gender, password, userType=0):
    password = hashlib.sha3_512(password.encode()).hexdigest()
    username = email.split("@")[0]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Users (UserID, Name, Address, Phone, Email, Age, Gender, InsuranceCompany, UserPhoto, Username, Password, DLPhotos, Usertype) VALUES (NULL, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL, ?)",
        (name, address, phone, email, age, gender, username, password, userType),
    )
    conn.commit()
    conn.close()

def update_customer_in_db(user_id, name, address, phone, email, age, gender, insurance_company, photo_filename):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Users SET Name = ?, Address = ?, Phone = ?, Email = ?, Age = ?, Gender = ?, InsuranceCompany = ?, UserPhoto = ? WHERE UserID = ?",
        (name, address, phone, email, age, gender, insurance_company, photo_filename, user_id),
    )
    conn.commit()
    conn.close()

def insert_customer(customer_data, username, password):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO Users (Name, Address, Phone, Email, Age, Gender, InsuranceCompany, UserPhoto, Username, Password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                customer_data['name'], customer_data['address'], customer_data['phone'], 
                customer_data['email'], customer_data['age'], customer_data['gender'],
                customer_data['insurance_company'], customer_data['photo'], username, password
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error inserting customer: {e}")
        raise

def mark_customer_inactive(user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET Active = ? WHERE UserID = ?", ("False", user_id))
    conn.commit()
    conn.close()

# ---------------------- Vehicle Management ----------------------

def get_vehicle_information():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicles WHERE Active = 'True'")
    data = cursor.fetchall()
    conn.close()
    return data

def get_vehicle_by_id(vehicle_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicles WHERE VehicleID = ?", (vehicle_id,))
    vehicle = cursor.fetchone()
    conn.close()
    return vehicle

def insert_vehicle(vehicle_data):
    try:
        serviceid = determine_service_id(vehicle_data['mileage'])
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO Vehicles (Make, Model, Year, Type, Mileage, Transmission, NumDoors, 
            RepairStatus, Available, Photos, LocationID, ServiceID, KeyFeatures, Description, DriveTrain)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                vehicle_data['make'], vehicle_data['model'], vehicle_data['year'], vehicle_data['type'],
                vehicle_data['mileage'], vehicle_data['transmission'], vehicle_data['numdoors'], 
                vehicle_data['repairstatus'], vehicle_data['available'], vehicle_data['photos'], 
                vehicle_data['locationid'], serviceid, vehicle_data['keyfeatures'], vehicle_data['description'], 
                vehicle_data['drivetrain']
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding vehicle: {e}")
        raise

def update_vehicle_in_db(vehicle_id, make, model, year, type, mileage, transmission, numdoors, repairstatus, available, photos, locationid, serviceid, keyfeatures, description, drivetrain):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE Vehicles SET Make = ?, Model = ?, Year = ?, Type = ?, Mileage = ?, Transmission = ?, NumDoors = ?, 
        RepairStatus = ?, Available = ?, Photos = ?, LocationID = ?, ServiceID = ?, KeyFeatures = ?, 
        Description = ?, DriveTrain = ? WHERE VehicleID = ?
        ''',
        (make, model, year, type, mileage, transmission, numdoors, repairstatus, available, photos, locationid, serviceid, keyfeatures, description, drivetrain, vehicle_id)
    )
    conn.commit()
    conn.close()

def mark_vehicle_inactive(vehicle_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Vehicles SET Active = ? WHERE VehicleID = ?", ("False", vehicle_id))
    conn.commit()
    conn.close()

# ---------------------- Reservation Management ----------------------

def make_reservation_db(vehicleid, planid, customerid, startdate, enddate, numdays, picklocation, droplocation, userID, totalprice):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO Reservations (VehicleID, UserID, PlanID, ReserveStartDate, ReserveEndDate, NumDays, 
        PickUpLocation, DropOffLocation, CustomerID, TotalPrice) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (vehicleid, userID, planid, startdate, enddate, numdays, picklocation, droplocation, customerid, totalprice)
    )
    conn.commit()
    conn.close()
    return True

def get_reservation_by_id(reservationid):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Reservations WHERE ReservationID = ?", (reservationid,))
    data = cursor.fetchone()
    conn.close()
    return data

def update_reservation_SA(ReservationID, fileloc):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Reservations SET ContractLocation = ?, SignedContract = 'True' WHERE ReservationID = ?", (fileloc, ReservationID))
    conn.commit()
    conn.close()
    return True

def drop_off_car(reservation_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT VehicleID FROM Reservations WHERE ReservationID = ?", (reservation_id,))
    vehicle_id = cursor.fetchone()[0]
    cursor.execute("UPDATE Vehicles SET Available = ? WHERE VehicleID = ?", ("Yes", vehicle_id))
    cursor.execute("UPDATE Vehicles SET LocationID = (SELECT DropOffLocation FROM Reservations WHERE ReservationID = ?) WHERE VehicleID = ?", (reservation_id, vehicle_id))
    cursor.execute("UPDATE Reservations SET DroppedOff = 'True' WHERE ReservationID = ?", (reservation_id,))
    conn.commit()
    conn.close()
    return True

# ---------------------- Invoice Management ----------------------

def make_invoice_db(planID, ReservationID, VehicleID, CustomerID):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO Invoice (PlanID, ReservationID, VehicleID, CustomerID) 
        VALUES (?, ?, ?, ?)
        ''', 
        (planID, ReservationID, VehicleID, CustomerID)
    )
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

# ---------------------- Vehicle Filtering and Availability ----------------------

def filter_vehicles(type, make, model, drive, transmission, location):
    type = "%" if type == "" else type
    make = "%" if make == "" else make
    model = "%" if model == "" else model
    drive = "%" if drive == "" else drive
    transmission = "%" if transmission == "" else transmission
    location = "%" if location == "" else location

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT * FROM Vehicles 
        WHERE Type LIKE ? AND Make LIKE ? AND Model LIKE ? 
        AND DriveTrain LIKE ? AND Transmission LIKE ? AND LocationID LIKE ?
        ''',
        (type, make, model, drive, transmission, location)
    )
    data = cursor.fetchall()
    conn.close()
    return data

def filter_vehicles_by_dates(type, make, model, drive, transmission, location, start_date, end_date):
    type = "%" if type == "" else type
    make = "%" if make == "" else make
    model = "%" if model == "" else model
    drive = "%" if drive == "" else drive
    transmission = "%" if transmission == "" else transmission
    location = "%" if location == "" else location

    formatted_start_date = f"{start_date[6:]}-{start_date[:2]}-{start_date[3:5]}"
    formatted_end_date = f"{end_date[6:]}-{end_date[:2]}-{end_date[3:5]}"

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

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        query,
        (type, make, model, drive, transmission, location, formatted_end_date, formatted_start_date)
    )
    data = cursor.fetchall()
    conn.close()
    return data

# ---------------------- Payment and Invoice Updates ----------------------

def updateinvoice(reservationid, payment):
    currentPaidAmount = float(get_invoice_PaidAmount(reservationid))
    payment += currentPaidAmount
    invoiceID = get_invoiceid_by_reservationid(reservationid)
    currentdate = datetime.now().strftime("%m/%d/%Y")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Invoice SET PaidAmount = ?, LastPaymentDate = ? WHERE InvoiceID = ?",
        (payment, currentdate, invoiceID)
    )
    conn.commit()

    total_price = get_reservation_totalprice(reservationid)
    if payment == total_price:
        cursor.execute("UPDATE Invoice SET PaymentStatus = 'Paid' WHERE InvoiceID = ?", (invoiceID,))
    elif payment < total_price:
        cursor.execute("UPDATE Invoice SET PaymentStatus = 'Partial' WHERE InvoiceID = ?", (invoiceID,))
    conn.commit()
    conn.close()

def updatemileage(reservationid, mileage):
    vehicleid = get_reservation_by_id(reservationid)[1]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Vehicles SET Mileage = ? WHERE VehicleID = ?", (mileage, vehicleid))
    conn.commit()
    conn.close()

# ---------------------- Utility Functions ----------------------

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

# ---------------------- Reservation and Customer Data Retrieval ----------------------

def get_reserved_dates(vehicle_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ReserveStartDate, ReserveEndDate FROM Reservations WHERE VehicleID = ?", (vehicle_id,))
    dates = cursor.fetchall()
    conn.close()
    return dates

def get_reservations_tableData(numRows=5, pickedup=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT ReservationID, VehicleID, ReserveStartDate, ReserveEndDate, InvoiceID, CustomerID, DroppedOff
        FROM Reservations
        WHERE PickedUp = ? AND DroppedOff = 'False'
        ORDER BY ReservationID DESC
        LIMIT ?
        ''',
        (str(pickedup), numRows)
    )
    data = cursor.fetchall()
    conn.close()
    return data

def get_customer_tableData(userEmail, pickedUp=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT ReservationID, VehicleID, ReserveStartDate, ReserveEndDate, InvoiceID, CustomerID, DroppedOff
        FROM Reservations
        WHERE CustomerID = (SELECT CustomerID FROM Customers WHERE Email = ?)
        AND PickedUp = ?
        ''',
        (userEmail, str(pickedUp))
    )
    data = cursor.fetchall()
    conn.close()
    return data

# ---------------------- Location and Customer Utilities ----------------------

def get_location_options():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT LocationID, Address FROM Locations")
    data = cursor.fetchall()
    conn.close()
    return data

def get_location_by_id(location_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Locations WHERE LocationID = ?", (location_id,))
    location = cursor.fetchone()
    conn.close()
    return location

def get_emailData_by_customerid(customer_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT Email FROM Customers WHERE CustomerID = ?", (customer_id,))
    data = cursor.fetchone()
    conn.close()
    return data[0] if data else None

def get_customerid_by_email(email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT CustomerID FROM Customers WHERE Email = ?", (email,))
    data = cursor.fetchone()
    conn.close()
    return data

def insert_customer_CustomerTable(name, address, phone, email, filename):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Customers (Name, Address, Phone, Email, DLPhoto) VALUES (?, ?, ?, ?, ?)", (name, address, phone, email, filename))
    conn.commit()
    conn.close()

# ---------------------- Payment and Pricing Utilities ----------------------

def get_reservation_totalprice(reservationid):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT TotalPrice FROM Reservations WHERE ReservationID = ?", (reservationid,))
    data = cursor.fetchone()
    conn.close()
    return data[0] if data else None

def get_invoice_PaidAmount(reservationid):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT PaidAmount FROM Invoice WHERE ReservationID = ?", (reservationid,))
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

def get_rates_by_vehicle_type(vehicle_type):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM RentalPlans WHERE Type = ?", (vehicle_type,))
    rates = cursor.fetchall()
    conn.close()
    return rates

# ---------------------- Reservation and Vehicle Updates ----------------------

def update_reservation_db(ReservationID, InvoiceID):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Reservations SET InvoiceID = ? WHERE ReservationID = ?", (InvoiceID, ReservationID))
    conn.commit()
    conn.close()
    return True

def update_reservation_SA(ReservationID, fileloc):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Reservations SET ContractLocation = ?, SignedContract = 'True' WHERE ReservationID = ?", (fileloc, ReservationID))
    conn.commit()
    conn.close()
    return True

def pick_up_car(reservation_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT r.ReservationID, r.SignedContract, r.VehicleID, r.PickUpLocation, l.LocationID
            FROM Reservations r
            JOIN Locations l ON r.PickUpLocation = l.LocationID
            WHERE r.ReservationID = ? AND r.PickedUp = 'False'
            ''',
            (reservation_id,)
        )
        result = cursor.fetchone()

        if result:
            reservation_id, signed_contract, vehicle_id, pickup_location, location_id = result

            if not signed_contract:
                return {"status": "Error", "message": "Please sign the rental agreement before picking up the vehicle."}
            cursor.execute("UPDATE Vehicles SET Available = ? WHERE VehicleID = ?", ("No", vehicle_id))
            cursor.execute("UPDATE Reservations SET PickedUp = 'True' WHERE ReservationID = ?", (reservation_id,))
            conn.commit()
    except Exception as e:
        print(f"Error in pick_up_car: {e}")
    finally:
        conn.close()

def drop_off_car(reservation_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT VehicleID FROM Reservations WHERE ReservationID = ?", (reservation_id,))
    vehicle_id = cursor.fetchone()[0]
    cursor.execute("UPDATE Vehicles SET Available = ? WHERE VehicleID = ?", ("Yes", vehicle_id))
    cursor.execute("UPDATE Vehicles SET LocationID = (SELECT DropOffLocation FROM Reservations WHERE ReservationID = ?) WHERE VehicleID = ?", (reservation_id, vehicle_id))
    cursor.execute("UPDATE Reservations SET DroppedOff = 'True' WHERE ReservationID = ?", (reservation_id,))
    conn.commit()
    conn.close()
    return True

def get_planid_by_vehicleid(vehicleid):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT rp.PlanID 
        FROM RentalPlans rp
        JOIN Vehicles v ON rp.Type = v.Type
        WHERE v.VehicleID = ?
        ''',
        (vehicleid,)
    )
    data = cursor.fetchone()
    conn.close()
    return data[0] if data else None

def get_reservationid_by_customerid(customerid, vehicleid, startdate, enddate):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT ReservationID 
        FROM Reservations 
        WHERE CustomerID = ? AND VehicleID = ? AND ReserveStartDate = ? AND ReserveEndDate = ?
        ''',
        (customerid, vehicleid, startdate, enddate)
    )
    data = cursor.fetchone()
    conn.close()
    return data[0] if data else None
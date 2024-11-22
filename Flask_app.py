# Flask and related modules
from flask import Flask, render_template, request, redirect, session, url_for, jsonify

# Database and security modules
import sqlite3
import hashlib

# Utility modules
import os
import json
from markupsafe import Markup
from datetime import datetime
from werkzeug.utils import secure_filename

# Custom modules
from utils import *
from generate import *
from sqlQueries import *

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'super secret key'

# Configure upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['ALLOWED_FILETYPES'] = {'pdf'}

# =============================
# 1. General Utility Functions
# =============================

def allowed_file(filename):
    """Check if the given filename has an allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def allowed_pdf(filename):
    """Check if the given filename has an allowed PDF extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_FILETYPES']

# ==============================================
# 2. Authentication and User Session Management
# ==============================================

@app.route("/")
def index():
    """Render the login page when the root URL is accessed."""
    return render_template("login.html")

@app.route("/login", methods=['POST'])
def login():
    """Authenticate a user by verifying their email and password."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        bool, modal = login_user(email, password)
        if bool:
            return redirect(url_for("products"))
        else:
            return render_template("login.html", modal=modal)

@app.route("/forgot_password", methods=['POST'])
def forgot_password():
    """Allow a user to reset their password by verifying their email and updating the database."""
    if request.method == 'POST':
        email = request.form['email_forgot']
        new_password = request.form['newpassword']
        confirm_password = request.form['confirmpassword']
        
        if new_password != confirm_password:
            modal = populateErrorModal("Passwords do not match")
            return render_template("login.html", modal=modal)
        
        if not check_password_meets_requirements(new_password):
            modal = populateErrorModal("Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number")
            return render_template("login.html", modal=modal)
        
        data = get_user(email)
        
        if data:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE Users SET Password = ? WHERE Email = ?", (hashlib.sha3_512(new_password.encode()).hexdigest(), email))
            conn.commit()
            conn.close()
            return render_template("login.html", modal=populateErrorModal("Password successfully updated", "Success!"))

@app.route("/logout", methods=['POST', 'GET'])
def logout():
    """Log out the current user by clearing their session data."""
    session.clear()
    return render_template("login.html")

# =======================================
# 3. User Navigation and Product Display
# =======================================

@app.route("/products", methods=['GET', 'POST'])
def products():
    """Display available products with filtering and sorting options."""
    if "UserID" not in session:
        return redirect(url_for("index"))

    selected_type = request.form.get('type', '') if request.method == 'POST' else ""
    selected_make = request.form.get('make', '') if request.method == 'POST' else ""
    selected_model = request.form.get('model', '') if request.method == 'POST' else ""
    selected_drive = request.form.get('drive', '') if request.method == 'POST' else ""
    selected_transmission = request.form.get('transmission', '') if request.method == 'POST' else ""
    selected_location = request.form.get('location', '') if request.method == 'POST' else ""
    
    selected_start_date = request.form.get('start_date', '') if request.method == 'POST' else ""
    if selected_start_date != "":
        start_date = datetime.strptime(selected_start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
    
    selected_end_date = request.form.get('end_date', '') if request.method == 'POST' else ""
    if selected_end_date != "":
        end_date = datetime.strptime(selected_end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
    
    if selected_start_date != "" and selected_end_date != "": 
        vehicle_data = filter_vehicles_by_dates(
            selected_type,
            selected_make,
            selected_model,
            selected_drive,
            selected_transmission,
            selected_location,
            start_date,
            end_date
        ) if request.method == 'POST' else get_vehicle_information()
    else:
        vehicle_data = (
            filter_vehicles(
                selected_type,
                selected_make,
                selected_model,
                selected_drive,
                selected_transmission,
                selected_location
            ) if request.method == 'POST' else get_vehicle_information()
        )

    vehicle_html = generate_vehicle_html(vehicle_data)
    options = generate_options(selected_type, selected_make, selected_model, selected_drive, selected_transmission, selected_location, vehicle_data)

    if session["Usertype"] == 1:
        return render_template("products.html", vehicle_html=vehicle_html, options=options, admin=admin_nav())

    return render_template("products.html", vehicle_html=vehicle_html, options=options)

@app.route('/vehicle/<int:vehicle_id>')
def vehicle_page(vehicle_id):
    """Display details for a specific vehicle based on its ID."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    vehicle = get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return "Vehicle not found", 404

    vehicle_data = {
        "images": vehicle[10].split("ㄹ"),
        "features": vehicle[13].split(","),
        "description": vehicle[14],
        "map_embed_link": get_location_by_id(vehicle[11])[3]
    }

    image_section = Markup("".join(
        f'<div class="swiper-slide" style="background: url(\'{url}\') center center / cover no-repeat; min-height: 800px;"></div>'
        for url in vehicle_data["images"]
    ))

    features_section = Markup("".join(
        f"<li>{feature}</li>" for feature in vehicle_data["features"]
    ))

    description_section = Markup(f"<p class='card-text'>{vehicle_data['description']}</p>")
    map_section = Markup(f'<iframe src="{vehicle_data["map_embed_link"]}" width="100%" height="300" style="border:0;" allowfullscreen="" loading="lazy"></iframe>')
    
    reserved_dates_db = get_reserved_dates(vehicle_id)
    fixed_dates = []
    
    if reserved_dates_db != []:
        for i in range(len(reserved_dates_db)):
            start_date_str = reserved_dates_db[i][0].strip()
            end_date_str = reserved_dates_db[i][1].strip()
            start_date = datetime.strptime(start_date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
            dates = generate_dates_between(start_date, end_date)
            fixed_dates += dates

    if session["reservedCars"] != "":
        reserved = session["reservedCars"].strip().split(";")
        for car in reserved:
            car = car.strip().split(",")
            if len(car) == 3 and car[0] == str(vehicle_id):
                dates = generate_dates_between(datetime.strptime(car[1].split(" - ")[0], "%m/%d/%Y").strftime("%Y-%m-%d"), datetime.strptime(car[1].split(" - ")[1], "%m/%d/%Y").strftime("%Y-%m-%d"))
                fixed_dates += dates
    
    if session["Usertype"] == 1:
        return render_template(
            'product.html',
            vehicleID=vehicle[0],
            year=vehicle[3],
            make=vehicle[1],
            model=vehicle[2],
            image_section=image_section,
            features_section=features_section,
            description_section=description_section,
            map_section=map_section,
            reserved_dates=json.dumps(fixed_dates),
            admin=admin_nav()
        )
    
    return render_template(
        'product.html',
        vehicleID=vehicle[0],
        year=vehicle[3],
        make=vehicle[1],
        model=vehicle[2],
        image_section=image_section,
        features_section=features_section,
        description_section=description_section,
        map_section=map_section,
        reserved_dates=json.dumps(fixed_dates)
    )

@app.route("/cart", methods=['POST', 'GET'])
def cart():
    """Display the user's cart with details of reserved vehicles, or show an empty cart message."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if not session.get("reservedCars"):
        if session["Usertype"] == 1:
            return render_template("shopping-cart.html", cart_html="Your cart is empty.", admin=admin_nav())
        return render_template("shopping-cart.html", cart_html="Your cart is empty.")
    
    cart_html = ""
    reservedCars = session["reservedCars"].strip().split(";")
    
    for car in reservedCars:
        car = car.strip().split(",")
        if len(car) == 3:
            vehicle = get_vehicle_by_id(car[0])
            cart_html += Markup(
                """<tr>
                    <th scope="row" class="border-0">
                        <div class="p-2">
                        <img src="{Photo}" alt="" width="70" class="img-fluid rounded shadow-sm">
                        <div class="ml-3 d-inline-block align-middle">
                            <h5 class="mb-0"> <a href="/vehicle/{VehicleID}" class="text-dark d-inline-block align-middle">{year} {make} {model}</a></h5><span class="text-muted font-weight-normal font-italic d-block">Type: {type}</span>
                        </div>
                        </div>
                    </th>
                    <td class="border-0 align-middle"><strong>{dates}</strong></td>
                    <td class="border-0 align-middle"><strong>{numDays}</strong></td>
                    <td class="border-0 align-middle"><a href="/remove/{ReserveID}" class="text-dark"><i class="fa fa-trash"></i></a></td>
                    </tr>"""
            ).format(Photo=vehicle[10].split("ㄹ")[0], year=vehicle[3], make=vehicle[1], model=vehicle[2], type=vehicle[4], dates=car[1], VehicleID=vehicle[0], numDays=getNumDays(car[1])+1, ReserveID=car[2])
            
    checkout_html, totalData = GetCheckoutValues(reservedCars)
    
    if session["Usertype"] == 1:
        return render_template("shopping-cart.html", cart_html=cart_html, Rates=checkout_html, subtotal=totalData[0], tax=totalData[1], total=totalData[2], admin=admin_nav())   
         
    return render_template("shopping-cart.html", cart_html=cart_html, Rates=checkout_html, subtotal=totalData[0], tax=totalData[1], total=totalData[2])

@app.route("/addToCart", methods=['POST'])
def addToCart():
    """Add a selected vehicle and date range to the user's cart."""
    if "UserID" not in session:
        return redirect(url_for("index"))

    vehicle_id = request.form['vehicleID']
    daterange = request.form['daterange']
    
    if "reservedCars" not in session or not session["reservedCars"]:
        session["reservedCars"] = ""
    
    reserve_id = 0

    if session["reservedCars"].strip() != "":
        reserved_cars = session["reservedCars"].strip().split(";")
        try:
            existing_ids = [
                int(car.strip().split(",")[2]) for car in reserved_cars if car.strip()
            ]
            reserve_id = max(existing_ids) + 1
        except (ValueError, IndexError):
            reserve_id = 0

    session["reservedCars"] += f"{vehicle_id},{daterange},{reserve_id};"

    return redirect(url_for("products"))

@app.route('/remove/<int:reserve_id>')
def remove_from_cart(reserve_id):
    """Remove a specific vehicle from the user's cart based on its reservation ID."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if not session.get("reservedCars"):   
        return redirect(url_for("products"))
    
    reservedCars = session["reservedCars"].strip().split(";")
    newReservedCars = ""
    
    for car in reservedCars:
        car = car.strip().split(",")
        if len(car) == 3 and car[2] != str(reserve_id):
            newReservedCars += car[0] + "," + car[1] + "," + car[2] + ";"
    
    session["reservedCars"] = newReservedCars
    
    if session["Usertype"] == 1:
        return redirect(url_for("cart"))
    return redirect(url_for("cart"))

# ====================
# 4. Admin Operations
# ====================

@app.route("/admin", methods=['POST', 'GET'])
def admin():
    """Render the admin dashboard if the user is logged in and has admin privileges."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    if session["Usertype"] == 1:
        username = session["Username"]
        
        locationOptions = get_location_options()
        locationOptions = generate_location_options(locationOptions)
        
        return render_template("admin.html", Username=username, admin=admin_nav(), locationOptions=locationOptions)
    else:
        return redirect(url_for("products"))

# =======================
# 5. Customer Management
# =======================

@app.route('/create_customer', methods=['POST'])
def create_customer():
    """Create a new customer profile, including uploading a photo."""
    if 'photo' not in request.files:
        return jsonify({'error': 'Photo file is required'}), 400
    
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'error': 'No selected photo'}), 400

    if photo and allowed_file(photo.filename):
        filename = secure_filename(photo.filename)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER']), exist_ok=True)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        customer_data = {
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'insurance_company': request.form.get('insurance_company'),
            'photo': filename
        }

        username = customer_data['email'].split('@')[0]
        password = hashlib.sha3_512("defaultpassword".encode()).hexdigest() 

        try:
            insert_customer(customer_data, username, password)
            return jsonify({'message': 'Customer created successfully!'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid photo file format'}), 400

@app.route('/get_customer_by_userid', methods=['POST'])
def get_customer_by_userid():
    """Retrieve customer information by their user ID."""
    data = request.get_json()
    user_id = data.get('userID')

    if not user_id:
        return jsonify({'error': 'UserID is required'}), 400

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE UserID = ?", (user_id,))
    customer = cursor.fetchone()
    conn.close()

    if customer:
        customer_data = {
            'name': customer[1],
            'address': customer[2],
            'phone': customer[3],
            'email': customer[4],
            'age': customer[5],
            'gender': customer[6],
            'insurance_company': customer[7],
            'photo': customer[8]
        }
        photo_url = url_for('static', filename=f'uploads/{customer[8]}') if customer[8] else None
        customer_data['photo_url'] = photo_url
        return jsonify({'customer': customer_data})
    else:
        return jsonify({'error': 'Customer not found'}), 404

@app.route('/modify_customer', methods=['POST'])
def modify_customer():
    """Modify an existing customer's details."""
    customer_data = request.json

    if 'userID' not in customer_data or not customer_data['userID']:
        return jsonify({'error': 'UserID is required'}), 400

    user_id = customer_data['userID']
    name = customer_data.get('name')
    address = customer_data.get('address')
    phone = customer_data.get('phone')
    email = customer_data.get('email')
    age = customer_data.get('age')
    gender = customer_data.get('gender')
    insurance_company = customer_data.get('insurance_company')
    new_photo = customer_data.get('photo')

    if new_photo:
        photo_filename = new_photo
    else:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT UserPhoto FROM Users WHERE UserID = ?", (user_id,))
            current_photo = cursor.fetchone()
            conn.close()

            if current_photo:
                photo_filename = current_photo[0]
            else:
                return jsonify({'error': 'User not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    try:
        update_customer_in_db(user_id, name, address, phone, email, age, gender, insurance_company, photo_filename)
        return jsonify({'message': 'Customer updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_customer', methods=['POST'])
def delete_customer():
    """Mark a customer as inactive rather than deleting their data."""
    data = request.json
    user_id = data.get('userID')

    if not user_id:
        return jsonify({'error': 'UserID is required'}), 400

    try:
        mark_customer_inactive(user_id)
        return jsonify({'message': 'Customer marked as inactive successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ======================
# 6. Vehicle Management
# ======================

@app.route('/create_vehicle', methods=['POST'])
def create_vehicle():
    """Add a new vehicle to the inventory with all its details."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    if session["Usertype"] != 1:
        return redirect(url_for("products"))
    if request.method == 'POST':
        vehicle_data = {
            'make': request.form.get('make'),
            'model': request.form.get('model'),
            'year': request.form.get('year'),
            'type': request.form.get('type'),
            'mileage': request.form.get('mileage'),
            'transmission': request.form.get('transmission'),
            'numdoors': request.form.get('numdoors'),
            'repairstatus': request.form.get('repairstatus'),
            'available': request.form.get('available'),
            'locationid': request.form.get('locationid'),
            'serviceid': request.form.get('serviceid'),
            'keyfeatures': request.form.get('keyfeatures'),
            'description': request.form.get('description'),
            'drivetrain': request.form.get('drivetrain'),
            'photos': request.form.get('photos')
        }

        try:
            insert_vehicle(vehicle_data)
            return jsonify({'message': 'Vehicle added successfully!'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return redirect(url_for("admin"))

@app.route('/get_vehicle_by_vehicleid', methods=['POST'])
def get_vehicle_by_vehicleid():
    """Retrieve vehicle information by its ID."""
    data = request.get_json()
    vehicle_id = int(data.get('vehicleID'))

    if not vehicle_id:
        return jsonify({'error': 'VehicleID is required'}), 400

    vehicle = get_vehicle_by_id(vehicle_id)

    if vehicle:
        vehicle_data = {
            'make': vehicle[1],
            'model': vehicle[2],
            'year': vehicle[3],
            'type': vehicle[4],
            'mileage': vehicle[5],
            'transmission': vehicle[6],
            'numdoors': vehicle[7],
            'repairstatus': vehicle[8],
            'available': vehicle[9],
            'photos': vehicle[10],
            'locationid': vehicle[11],
            'serviceid': vehicle[12],
            'keyfeatures': vehicle[13],
            'description': vehicle[14],
            'drivetrain': vehicle[15]
        }
        return jsonify({'vehicle': vehicle_data})
    else:
        return jsonify({'error': 'Vehicle not found'}), 404

@app.route('/modify_vehicle', methods=['POST'])
def modify_vehicle():
    """Update an existing vehicle's details."""
    vehicle_data = request.json

    if 'vehicleID' not in vehicle_data or not vehicle_data['vehicleID']:
        return jsonify({'error': 'VehicleID is required'}), 400

    vehicle_id = vehicle_data['vehicleID']
    make = vehicle_data.get('make')
    model = vehicle_data.get('model')
    year = vehicle_data.get('year')
    type = vehicle_data.get('type')
    mileage = vehicle_data.get('mileage')
    transmission = vehicle_data.get('transmission')
    numdoors = vehicle_data.get('numdoors')
    repairstatus = vehicle_data.get('repairstatus')
    available = vehicle_data.get('available')
    photos = vehicle_data.get('photo')  
    locationid = vehicle_data.get('locationid')
    serviceid = vehicle_data.get('serviceid')
    keyfeatures = vehicle_data.get('keyfeatures')
    description = vehicle_data.get('description')
    drivetrain = vehicle_data.get('drivetrain')

    try:
        update_vehicle_in_db(vehicle_id, make, model, year, type, mileage, transmission, numdoors, repairstatus, available, photos, locationid, serviceid, keyfeatures, description, drivetrain)
        return jsonify({'message': 'Vehicle updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_vehicle', methods=['POST'])
def delete_vehicle():
    """Mark a vehicle as inactive instead of deleting it."""
    data = request.json
    vehicle_id = data.get('vehicleID')

    if not vehicle_id:
        return jsonify({'error': 'VehicleID is required'}), 400

    try:
        mark_vehicle_inactive(vehicle_id)
        return jsonify({'message': 'Vehicle marked as inactive successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =================================
# 7. Reservations and Transactions
# =================================

@app.route('/makereservation', methods=['POST', 'GET'])
def make_reservation():
    """Create a reservation for selected vehicles and store all details in the database."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if not session.get("reservedCars"):
        return redirect(url_for("products"))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        dropofflocation = request.form['dropofflocation']

        reservedCars = session["reservedCars"].strip().split(";")
        driversLicensePhoto = request.files['driversLicensePhoto']
        if driversLicensePhoto.filename == '':
            return jsonify({'error': 'No selected photo'}), 400
        
        if driversLicensePhoto and allowed_file(driversLicensePhoto.filename):
            filename = name + phone + ".jpg"
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER']+"driversLicense/"), exist_ok=True)
            driversLicensePhoto.save(os.path.join(app.config['UPLOAD_FOLDER']+"driversLicense/", filename))
        else:
            return jsonify({'error': 'Invalid photo file format'}), 400
        
        insert_customer_CustomerTable(name, address, phone, email, filename)
        customerid = get_customerid_by_email(email)
        
        for car in reservedCars:
            car = car.strip().split(",")
            if len(car) == 3:
                vehicle_id = car[0]
                daterange = car[1]
                startdate = datetime.strptime(daterange.split(" - ")[0], "%m/%d/%Y").strftime("%m/%d/%Y")
                enddate = datetime.strptime(daterange.split(" - ")[1], "%m/%d/%Y").strftime("%m/%d/%Y")
                numdays = getNumDays(daterange) + 1
                priceforvehicle = get_price_by_vehicleid(int(vehicle_id), numdays)
                planID = get_planid_by_vehicleid(int(vehicle_id))
                location = get_vehicle_by_id(int(vehicle_id))[11]
                success = make_reservation_db(int(vehicle_id), planID, customerid[0], startdate, enddate, numdays, location, dropofflocation, userID=session['UserID'], totalprice=priceforvehicle)
                if not success:
                    return jsonify({'error': 'Failed to make reservation'}), 500
                
        for car in reservedCars:
            car = car.strip().split(",")
            if len(car) == 3:
                daterange = car[1]
                startdate = datetime.strptime(daterange.split(" - ")[0], "%m/%d/%Y").strftime("%m/%d/%Y")
                enddate = datetime.strptime(daterange.split(" - ")[1], "%m/%d/%Y").strftime("%m/%d/%Y")
                reservationid = get_reservationid_by_customerid(customerid[0], car[0], startdate, enddate)
                planID = get_planid_by_vehicleid(car[0])
                success = make_invoice_db(planID, reservationid, car[0], customerid[0])
                invoiceID = get_invoiceid_by_reservationid(reservationid)
                update_reservation_db(reservationid, invoiceID)
                if not success:
                    return jsonify({'error': 'Failed to make invoice'}), 500
                
        session["reservedCars"] = ""
        return redirect(url_for("products"))
    else:
        cart = ""
        reservedCars = session["reservedCars"].strip().split(";")
        
        for car in reservedCars:
            car = car.strip().split(",")
            if len(car) == 3:
                vehicle = get_vehicle_by_id(car[0])
                cart += Markup(
                    """<tr>
                            <th scope="row" class="border-0">
                                <div class="p-2">
                                <img src="{Photo}" alt="" width="70" class="img-fluid rounded shadow-sm">
                                <div class="ml-3 d-inline-block align-middle">
                                    <h5 class="mb-0"> <a href="/vehicle/{VehicleID}" class="text-dark d-inline-block align-middle">{year} {make} {model}</a></h5><span class="text-muted font-weight-normal font-italic d-block">Type: {type}</span>
                                </div>
                                </div>
                            </th>
                            <td class="border-0 align-middle"><strong>{dates}</strong></td>
                            <td class="border-0 align-middle"><strong>{numDays}</strong></td>
                        </tr>"""
                ).format(Photo=vehicle[10].split("ㄹ")[0], year=vehicle[3], make=vehicle[1], model=vehicle[2], type=vehicle[4], dates=car[1], VehicleID=vehicle[0], numDays=getNumDays(car[1])+1)
                
        locationOptions = get_location_options()
        locationOptions = generate_location_options(locationOptions)
                
        if session["Usertype"] == 1:
            return render_template("make-reservation.html", cart=cart, locationOptions=locationOptions, admin=admin_nav())
        return render_template("make-reservation.html", cart=cart, locationOptions=locationOptions)

@app.route('/pickupdropoff', methods=['POST', 'GET'])
def pickupdropoff():
    """Manage pickup and drop-off operations for reservations, including email-based search."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    pickupHTML = ""
    dropoffHTML = ""
    pickup_modalhtml = ""
    dropoff_modalhtml = ""
    
    if request.method == 'POST':
        pickupEmail = request.form.get('pickupemail')
        dropoffEmail = request.form.get('dropoffemail')
        
        if pickupEmail != "":
            reservationsTableData = get_customer_tableData(pickupEmail)
            for i, reservation in enumerate(reservationsTableData):
                pickup_modalhtml += pickup_modal_html(reservation[0])
                reservation = list(reservation)
                email = get_emailData_by_customerid(reservation[5])
                reservation.append(email)
                reservationsTableData[i] = reservation
            pickupHTML = generate_pickupdropoff_html(reservationsTableData)
            
            reservationsTableData = get_reservations_tableData(pickedup=True)
            for i, reservation in enumerate(reservationsTableData):
                dropoff_modalhtml += dropoff_modal_html(reservation[0])
                reservation = list(reservation)
                email = get_emailData_by_customerid(reservation[5])
                reservation.append(email)
                reservationsTableData[i] = reservation
            dropoffHTML = generate_pickupdropoff_html(reservationsTableData)
            
            if session["Usertype"] == 1:
                return render_template("pickup-dropoff.html", admin=admin_nav(), pickupHTML=pickupHTML, dropoffHTML=dropoffHTML, pickup_modal_html=pickup_modalhtml, dropoff_modal_html=dropoff_modalhtml)
            return render_template("pickup-dropoff.html", pickupHTML=pickupHTML, dropoffHTML=dropoffHTML, pickup_modal_html=pickup_modal_html, dropoff_modal_html=dropoff_modal_html)
            
        elif dropoffEmail != "":
            reservationsTableData = get_reservations_tableData()
            for i, reservation in enumerate(reservationsTableData):
                pickup_modalhtml += pickup_modal_html(reservation[0])
                reservation = list(reservation)
                email = get_emailData_by_customerid(reservation[5])
                reservation.append(email)
                reservationsTableData[i] = reservation
            pickupHTML = generate_pickupdropoff_html(reservationsTableData)
            
            reservationsTableData = get_customer_tableData(dropoffEmail, True)
            for i, reservation in enumerate(reservationsTableData):
                dropoff_modalhtml += dropoff_modal_html(reservation[0])
                reservation = list(reservation)
                email = get_emailData_by_customerid(reservation[5])
                reservation.append(email)
                reservationsTableData[i] = reservation
            dropoffHTML = generate_pickupdropoff_html(reservationsTableData)
            
            if session["Usertype"] == 1:
                return render_template("pickup-dropoff.html", admin=admin_nav(), pickupHTML=pickupHTML, dropoffHTML=dropoffHTML, pickup_modal_html=pickup_modalhtml, dropoff_modal_html=dropoff_modalhtml)
            return render_template("pickup-dropoff.html", pickupHTML=pickupHTML, dropoffHTML=dropoffHTML, pickup_modal_html=pickup_modalhtml, dropoff_modal_html=dropoff_modalhtml)

    else:
        reservationsTableData = get_reservations_tableData()
        for i, reservation in enumerate(reservationsTableData):
            pickup_modalhtml += pickup_modal_html(reservation[0])
            reservation = list(reservation)
            email = get_emailData_by_customerid(reservation[5])
            reservation.append(email)
            reservationsTableData[i] = reservation
        pickupHTML = generate_pickupdropoff_html(reservationsTableData)

        reservationsTableData = get_reservations_tableData(pickedup=True)
        for i, reservation in enumerate(reservationsTableData):
            dropoff_modalhtml += dropoff_modal_html(reservation[0])
            reservation = list(reservation)
            email = get_emailData_by_customerid(reservation[5])
            reservation.append(email)
            reservationsTableData[i] = reservation
        dropoffHTML = generate_pickupdropoff_html(reservationsTableData)

    if session["Usertype"] == 1:
        return render_template("pickup-dropoff.html", admin=admin_nav(), pickupHTML=pickupHTML, dropoffHTML=dropoffHTML, pickup_modal_html=pickup_modalhtml, dropoff_modal_html=dropoff_modalhtml)
    return render_template("pickup-dropoff.html", pickupHTML=pickupHTML, dropoffHTML=dropoffHTML, pickup_modal_html=pickup_modal_html, dropoff_modal_html=dropoff_modal_html)

@app.route('/pickup/<int:reservation_id>', methods=['POST', 'GET'])
def pickup_car_route(reservation_id):
    """Mark a vehicle as picked up for a given reservation ID."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    pick_up_car(reservation_id) 

    return redirect(request.referrer)

@app.route('/dropoff/<int:reservation_id>', methods=['POST', 'GET'])
def dropoff_car_route(reservation_id):
    """Mark a vehicle as dropped off for a given reservation ID."""
    if "UserID" not in session:
        return redirect(url_for("index"))

    success = drop_off_car(reservation_id)
    if not success:
        return jsonify({'error': 'Failed to drop off car'}), 500
    
    return redirect(url_for("pickupdropoff"))

@app.route('/updateReservation/<int:reservationid>', methods=['POST'])
def updateReservation(reservationid):
    """Update payment and mileage details for a reservation."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if request.method == 'POST':
        payment = request.form['paymentamount']
        mileage = request.form['mileage']
        
        updateinvoice(reservationid, float(payment))
        updatemileage(reservationid, mileage)
        
        return redirect(url_for("pickupdropoff"))
    else:
        return redirect(url_for("pickupdropoff"))

# =============================
# 8. File Handling and Uploads
# =============================

@app.route('/uploadRentalAgreement/<int:ReservationID>', methods=['POST'])
def uploadRentalAgreement(ReservationID):
    """Upload a rental agreement file for a specific reservation."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if request.method == 'POST':
        rentalAgreement = request.files['rentalAgreement']
        if rentalAgreement.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if rentalAgreement and allowed_pdf(rentalAgreement.filename):
            filename = secure_filename(rentalAgreement.filename)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER']+f"Reservation_{ReservationID}/"), exist_ok=True)
            rentalAgreement.save(os.path.join(app.config['UPLOAD_FOLDER']+f"Reservation_{ReservationID}/", filename))
        else:
            return jsonify({'error': 'Invalid file format'}), 400
        
        fileloc = app.config['UPLOAD_FOLDER']+f"Reservation_{ReservationID}/"+filename
        success = update_reservation_SA(ReservationID, fileloc)
        if success:
            return redirect(url_for("pickupdropoff"))
        else:
            return jsonify({'error': 'Failed to upload rental agreement'}), 500

# =================================
# 9. Report and Invoice Generation
# =================================

@app.route("/generate_report", methods=["POST"])
def generate_report():
    """Generate a report of vehicle reservations within a specified date range."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    if session["Usertype"] != 1:
        return redirect(url_for("products"))
    
    startDate = request.form.get('startDate')
    endDate = request.form.get('endDate')

    if not startDate or not endDate:
        return jsonify({'error': 'Both startDate and endDate are required'}), 400
    
    return vehicleReport(startDate, endDate)

@app.route('/GenerateRentalAgreement/<int:reservation_id>')
def GenerateRentalAgreement(reservation_id):
    """Generate a rental agreement document for a given reservation."""
    if "UserID" not in session:
        return redirect(url_for("index"))
        
    return rentalAgreement(reservation_id)

@app.route('/GenerateInvoice')
def GenerateInvoice():
    """Generate an invoice for a reservation."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    reservation_id = 1
    return invoiceFromReservation(reservation_id)

@app.route('/generateRentalBill/<int:reservationid>', methods=['POST', 'GET'])
def generateRentalBill(reservationid):
    """Generate a rental bill for a specific reservation."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    return invoiceForSingleVehicle(reservationid) 

@app.route('/generateConsolidatedRentalBill/<int:reservationid>', methods=['POST', 'GET'])
def generateConsolidatedRentalBill(reservationid):
    """Generate a consolidated rental bill for multiple vehicles in a reservation."""
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    return invoiceFromReservation(reservationid)  

# =====================
# 10. Main Entry Point
# =====================

if __name__ == '__main__':
    """Run the Flask application in debug mode."""
    app.run(debug=True)
# Import necessary modules
from flask import Flask, render_template, request, redirect, session, url_for, jsonify  # Flask framework components
import sqlite3  # SQLite database interface
from markupsafe import Markup  # HTML sanitization for safe HTML rendering
import hashlib  # For hashing passwords
from datetime import datetime  # For date calculations
import json  # For JSON data handling
import os  # For file operations
from werkzeug.utils import secure_filename # For secure file uploads
import generate # For generating PDF reports
from utils import *  # For utility functions
from sqlQueries import *  # For database queries


# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'super secret key'  # Secret key for session management

# Configure upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Allowed extensions are already defined in the config
def allowed_file(filename):
    """
    Check if the file extension is allowed.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

   
# Route for login page
@app.route("/")
def index():
    return render_template("login.html")


# Route for vehicle listings and filtering
@app.route("/products", methods=['GET', 'POST'])
def products():
    # Check if user is logged in, redirect if not
    if "UserID" not in session:
        return redirect(url_for("index"))

    # Store selected filter values from the form (POST) or default values (GET)
    selected_type = request.form.get('type', '') if request.method == 'POST' else ""
    selected_make = request.form.get('make', '') if request.method == 'POST' else ""
    selected_model = request.form.get('model', '') if request.method == 'POST' else ""
    selected_drive = request.form.get('drive', '') if request.method == 'POST' else ""
    selected_transmission = request.form.get('transmission', '') if request.method == 'POST' else ""
    selected_location = request.form.get('location', '') if request.method == 'POST' else ""
    
    selected_start_date = request.form.get('start_date', '') if request.method == 'POST' else ""
    if selected_start_date != "": start_date = datetime.strptime(selected_start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
    
    selected_end_date = request.form.get('end_date', '') if request.method == 'POST' else ""
    if selected_end_date != "": end_date = datetime.strptime(selected_end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
    
    if selected_start_date != "" and selected_end_date != "": 
        # Retrieve filtered or all vehicle data with availability between selected dates
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
        # Retrieve filtered or all vehicle data
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

    # Generate HTML for vehicle display and options for filters
    vehicle_html = generate_vehicle_html(vehicle_data)
    options = generate_options(selected_type, selected_make, selected_model, selected_drive, selected_transmission, selected_location, vehicle_data)

    if session["Usertype"] == 1:
        return render_template("products.html", vehicle_html=vehicle_html, options=options, admin=admin_nav())

    return render_template("products.html", vehicle_html=vehicle_html, options=options)


# Route for displaying details of a specific vehicle
@app.route('/vehicle/<int:vehicle_id>')
def vehicle_page(vehicle_id):
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    # Retrieve vehicle information by ID
    vehicle = get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return "Vehicle not found", 404

    # Structure data for vehicle display page
    vehicle_data = {
        "images": vehicle[10].split("ㄹ"),
        "features": vehicle[13].split(","),
        "description": vehicle[14],
        "map_embed_link": get_location_by_id(vehicle[11])[3]
    }

    # Render HTML sections for images, features, description, and map
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
            # Strip any extra spaces and ensure the format is consistent
            start_date_str = reserved_dates_db[i][0].strip()
            end_date_str = reserved_dates_db[i][1].strip()

            # Parse and reformat the dates
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


# Route for login handling
@app.route("/login", methods=['POST'])
def login():  
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


# Route for logging out the user
@app.route("/logout", methods=['POST', 'GET'])
def logout():
    session.clear()  # Clear session data
    return render_template("login.html")


# Route for handling new user sign-up
@app.route("/signup", methods=['POST'])
def signup():
    return redirect(url_for("products"))


@app.route("/admin", methods=['POST', 'GET'])
def admin():
    if "UserID" not in session:
        return redirect(url_for("index"))
    if session["Usertype"] == 1:
        username = session["Username"]
        return render_template("admin.html", Username=username, admin=admin_nav())
    else:
        return redirect(url_for("products"))


@app.route("/addToCart", methods=['POST'])
def addToCart():
    if "UserID" not in session:
        return redirect(url_for("index"))

    vehicle_id = request.form['vehicleID']
    daterange = request.form['daterange']
    
    # Initialize reservedCars session variable if not set
    if "reservedCars" not in session or not session["reservedCars"]:
        session["reservedCars"] = ""
    
    reserve_id = 0

    # Check if there are existing reservations
    if session["reservedCars"].strip() != "":
        reserved_cars = session["reservedCars"].strip().split(";")
        try:
            # Extract all existing reserve IDs and find the maximum
            existing_ids = [
                int(car.strip().split(",")[2]) for car in reserved_cars if car.strip()
            ]
            reserve_id = max(existing_ids) + 1
        except (ValueError, IndexError):
            reserve_id = 0  # Reset reserve_id if parsing fails

    # Store reservation details in session
    session["reservedCars"] += f"{vehicle_id},{daterange},{reserve_id};"

    return redirect(url_for("products"))


# Route for removing a vehicle from the cart
@app.route('/remove/<int:reserve_id>')
def remove_from_cart(reserve_id):
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if not session.get("reservedCars"):   
        return redirect(url_for("products"))
    
    reservedCars = session["reservedCars"].strip().split(";")
    newReservedCars = ""
    
    for car in reservedCars:
        car = car.strip().split(",")
        if len(car) == 3 and car[2] != str(reserve_id):  # Check reserve_id in the 3rd column
            newReservedCars += car[0] + "," + car[1] + "," + car[2] + ";"
    
    session["reservedCars"] = newReservedCars
    
    if session["Usertype"] == 1:
        return redirect(url_for("cart"))
    return redirect(url_for("cart"))


# Route to display cart contents
@app.route("/cart", methods=['POST', 'GET'])
def cart():
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
         
    return render_template("shopping-cart.html", cart_html=cart_html, Rates=checkout_html, subtotal=totalData[0], tax=totalData[1], total=totalData[2] )


@app.route("/generate_report")
def generate_report():
    # Check if user is logged in
    if "UserID" not in session:
        return redirect(url_for("index"))
    if session["Usertype"] != 1:
        return redirect(url_for("products"))
    
    return generate.vehicleReport()


@app.route('/create_customer', methods=['POST'])
def create_customer():
    # Ensure the form data is sent as a file and handle the file upload
    if 'photo' not in request.files:
        return jsonify({'error': 'Photo file is required'}), 400
    
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'error': 'No selected photo'}), 400

    # Check if the photo file has an allowed extension
    if photo and allowed_file(photo.filename):
        # Secure the filename and save it to the uploads directory
        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Save to 'uploads/' folder

        # Now gather other customer details from the form data
        customer_data = {
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'insurance_company': request.form.get('insurance_company'),
            'photo': filename  # Store the filename in the database
        }

        # Add dummy values for Username and Password
        username = customer_data['email'].split('@')[0]  # Use email prefix as username
        password = hashlib.sha3_512("defaultpassword".encode()).hexdigest() 

        try:
            # Call insert_customer function with the required arguments
            insert_customer(customer_data, filename, username, password)
            return jsonify({'message': 'Customer created successfully!'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid photo file format'}), 400
    
    
@app.route('/create_vehicle', methods=['POST'])
def create_vehicle():
    if "UserID" not in session:
        return redirect(url_for("index"))
    if session["Usertype"] != 1:
        return redirect(url_for("products"))
    if request.method == 'POST':
        
        # Now gather other customer details from the form data
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
            # Call insert_customer function with the required arguments
            insert_vehicle(vehicle_data)
            return jsonify({'message': 'Vehicle added successfully!'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return redirect(url_for("admin"))
    
    
@app.route('/get_customer_by_userid', methods=['POST'])
def get_customer_by_userid():
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
            'photo': customer[8]  # Assuming photo filename is stored in column 8
        }
        # Assuming the photos are stored in a folder accessible via '/static/uploads/'
        photo_url = url_for('static', filename=f'uploads/{customer[8]}') if customer[8] else None

        customer_data['photo_url'] = photo_url

        return jsonify({'customer': customer_data})
    else:
        return jsonify({'error': 'Customer not found'}), 404
    
    
@app.route('/get_vehicle_by_vehicleid', methods=['POST'])
def get_vehicle_by_vehicleid():
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

@app.route('/modify_customer', methods=['POST'])
def modify_customer():
    customer_data = request.json  # Get the JSON payload from the frontend

    # Ensure that the UserID is provided
    if 'userID' not in customer_data or not customer_data['userID']:
        return jsonify({'error': 'UserID is required'}), 400

    # Get the UserID and other customer data
    user_id = customer_data['userID']
    name = customer_data.get('name')
    address = customer_data.get('address')
    phone = customer_data.get('phone')
    email = customer_data.get('email')
    age = customer_data.get('age')
    gender = customer_data.get('gender')
    insurance_company = customer_data.get('insurance_company')
    new_photo = customer_data.get('photo')  # New photo filename or empty if not updated

    # If a new photo is provided, use it; otherwise, retain the existing photo
    if new_photo:
        photo_filename = new_photo
    else:
        # Query the current photo filename from the database if no new photo is provided
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT UserPhoto FROM Users WHERE UserID = ?", (user_id,))
            current_photo = cursor.fetchone()
            conn.close()

            if current_photo:
                photo_filename = current_photo[0]  # Use the existing photo filename
            else:
                return jsonify({'error': 'User not found'}), 404

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Update the customer data in the database using the `update_customer_in_db` function
    try:
        update_customer_in_db(user_id, name, address, phone, email, age, gender, insurance_company, photo_filename)
        return jsonify({'message': 'Customer updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/modify_vehicle', methods=['POST'])
def modify_vehicle():
    vehicle_data = request.json  # Get the JSON payload from the frontend

    # Ensure that the UserID is provided
    if 'vehicleID' not in vehicle_data or not vehicle_data['vehicleID']:
        return jsonify({'error': 'VehicleID is required'}), 400

    # Get the UserID and other customer data
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

    # Update the vehicle data in the database using the `update_vehicle_in_db` function
    try:
        update_vehicle_in_db(vehicle_id, make, model, year, type, mileage, transmission, numdoors, repairstatus, available, photos, locationid, serviceid, keyfeatures, description, drivetrain)
        return jsonify({'message': 'Vehicle updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_customer', methods=['POST'])
def delete_customer():
    data = request.json  # Get the JSON payload from the frontend
    user_id = data.get('userID')

    # Ensure that the UserID is provided
    if not user_id:
        return jsonify({'error': 'UserID is required'}), 400

    # Update the "Active" status of the customer to "False" instead of deleting
    try:
        mark_customer_inactive(user_id)
        return jsonify({'message': 'Customer marked as inactive successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/set_session/<int:user_id>")
def set_session(user_id):
    session["UserID"] = user_id
    print(f"Session after setting: {dict(session)}")  # Debug log
    return jsonify({"message": f"Session set for UserID {user_id}"})

  
@app.route("/debug_session")
def debug_session():
    return jsonify(dict(session))

  
# Route to pick up a car
@app.route('/pickup', methods=['POST', 'GET'])
def pickup_car_route(user_id):
    # Check if the user is logged in and redirect if not
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    user_id = session["UserID"]

    result = pick_up_car(user_id)

    # Prepare context for rendering
    context = {
        "pickupHTML": "",
        "dropoffHTML": "",
        "pickup_message": None,
    }

    if result["status"] == "UnsignedContract":
        return redirect(url_for('GenerateRentalAgreement', reservation_id=result["reservation_id"]))

    if result["status"] == "Success":
        context["pickup_message"] = "Car picked up successfully!"

    if result["status"] == "NoReservation":
        context["pickup_message"] = "No active reservations found."

    return render_template("pickup-dropoff.html", **context)
         
@app.route('/dropoff', methods=['POST', 'GET'])
def dropoff_car_route():
    if "UserID" not in session:
        return redirect(url_for("index"))

    user_id = session["UserID"]
    context = {
        "pickupHTML": "",
        "dropoffHTML": "",
        "dropoff_message": None,
    }

    if request.method == "POST":
        try:
            # Get new mileage from the form
            new_mileage = request.form.get("new_mileage", type=int)
            if not new_mileage or new_mileage <= 0:
                context["dropoff_message"] = "Invalid or missing mileage value."
                return render_template("pickup-dropoff.html", **context)

            # Perform drop-off and prepare invoice
            result = drop_off_car(user_id, new_mileage)

            if result["status"] == "Success":
                context["dropoff_message"] = result["message"]

                # Generate invoice

            elif result["status"] == "NoReservation":
                context["dropoff_message"] = "No active reservations found for drop-off."

            return render_template("pickup-dropoff.html", **context)

        except Exception as e:
            context["dropoff_message"] = f"Server error: {str(e)}"
            return render_template("pickup-dropoff.html", **context)

    return render_template("pickup-dropoff.html", **context)
      
      
@app.route('/delete_vehicle', methods=['POST'])
def delete_vehicle():
    data = request.json  # Get the JSON payload from the frontend
    vehicle_id = data.get('vehicleID')

    # Ensure that the UserID is provided
    if not vehicle_id:
        return jsonify({'error': 'VehicleID is required'}), 400

    # Update the "Active" status of the customer to "False" instead of deleting
    try:
        mark_vehicle_inactive(vehicle_id)
        return jsonify({'message': 'Vehicle marked as inactive successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500  
    

@app.route('/makereservation', methods=['POST', 'GET'])
def make_reservation():
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if not session.get("reservedCars"):
        return redirect(url_for("products"))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        
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
        
        insert_customer(name, address, phone, email, filename)
        
        customerid = get_customerid_by_email(email)
        
        _,total = GetCheckoutValues(reservedCars)
        
        for car in reservedCars:
            car = car.strip().split(",")
            if len(car) == 3:
                vehicle_id = car[0]
                daterange = car[1]
                
                startdate = datetime.strptime(daterange.split(" - ")[0], "%m/%d/%Y").strftime("%m/%d/%Y")
                enddate = datetime.strptime(daterange.split(" - ")[1], "%m/%d/%Y").strftime("%m/%d/%Y")
                
                numdays = getNumDays(daterange) + 1
                
                planID = get_planid_by_vehicleid(int(vehicle_id))
                location = get_vehicle_by_id(int(vehicle_id))[11]
                success = make_reservation_db(int(vehicle_id), planID, customerid[0], startdate, enddate, numdays, location, userID=session['UserID'], totalprice=total[2])
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
                
        if session["Usertype"] == 1:
            return render_template("make-reservation.html", cart=cart, admin=admin_nav())
        return render_template("make-reservation.html", cart=cart)


@app.route('/pickupdropoff', methods=['POST', 'GET'])
def pickupdropoff():
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    pickupHTML = ""
    dropoffHTML = ""
    
    if request.method == 'POST':
        pass

    else:
        reservationsTableData = get_reservations_tableData()
        for i, reservation in enumerate(reservationsTableData):
            reservation = list(reservation)  # Convert tuple to list
            email = get_emailData_by_customerid(reservation[5])
            reservation.append(email)
            reservationsTableData[i] = reservation  # Update the list with the modified reservation
        pickupHTML = generate_pickupdropoff_html(reservationsTableData)

        reservationsTableData = get_reservations_tableData(True)
        for i, reservation in enumerate(reservationsTableData):
            reservation = list(reservation)  # Convert tuple to list
            email = get_emailData_by_customerid(reservation[5])
            reservation.append(email)
            reservationsTableData[i] = reservation  # Update the list with the modified reservation
        dropoffHTML = generate_pickupdropoff_html(reservationsTableData)

    if session["Usertype"] == 1:
        return render_template("pickup-dropoff.html", admin=admin_nav(), pickupHTML=pickupHTML, dropoffHTML=dropoffHTML)
    return render_template("pickup-dropoff.html", pickupHTML=pickupHTML, dropoffHTML=dropoffHTML)


@app.route('/GenerateRentalAgreement')
def GenerateRentalAgreement():
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    reservation_id = 2
    return generate.rentalAgreement(reservation_id)

# Main entry point for the Flask app
if __name__ == '__main__':
    app.run(debug=True)

# Import necessary modules
from flask import Flask, render_template, request, redirect, session, url_for, jsonify  # Flask framework components
import sqlite3  # SQLite database interface
from markupsafe import Markup  # HTML sanitization for safe HTML rendering
import hashlib  # For hashing passwords
from datetime import datetime  # For date calculations
import json  # For JSON data handling
import os  # For file operations
from werkzeug.utils import secure_filename # For secure file uploads
import report # For generating PDF reports
from utils import *  # For utility functions
from sqlQueries import *  # For database queries


# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'super secret key'  # Secret key for session management

# Configure upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

@app.route("/set_session/<int:user_id>")
def set_session(user_id):
    session["UserID"] = user_id
    print(f"Session after setting: {dict(session)}")  # Debug log
    return jsonify({"message": f"Session set for UserID {user_id}"})

@app.route("/debug_session")
def debug_session():
    return jsonify(dict(session))

# Route to pick up a car
@app.route("/pickup/<int:user_id>", methods=['POST'])
def pickup_car_route(user_id):
    if "UserID" not in session or session["UserID"] != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        success = pick_up_car(user_id)
        if success:
            return jsonify({'message': 'Car picked up successfully!'}), 200
        else:
            return jsonify({'error': 'No valid reservation found for pickup'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to drop off a car
@app.route("/dropoff/<int:user_id>", methods=['POST'])
def dropoff_car_route(user_id):
    if "UserID" not in session or session["UserID"] != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        success = drop_off_car(user_id)
        if success:
            return jsonify({'message': 'Car dropped off successfully!'}), 200
        else:
            return jsonify({'error': 'No valid reservation found for dropoff'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
   
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
    
    print(vehicle[10])

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
            ).format(Photo=vehicle[10].split("ㄹ")[0], year=vehicle[3], make=vehicle[1], model=vehicle[2], type=vehicle[4], dates=car[1], VehicleID=vehicle[0], numDays=getNumDays(car[1]), ReserveID=car[2])
            
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
    
    return report.generate()


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
        password = hashlib.sha3_512("defaultpassword".encode()).hexdigest()  # Dummy password

        try:
            # Call insert_customer function with the required arguments
            insert_customer(customer_data, filename, username, password)
            return jsonify({'message': 'Customer created successfully!'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid photo file format'}), 400
    
    
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
    
    
     
# Allowed extensions are already defined in the config
def allowed_file(filename):
    """
    Check if the file extension is allowed.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
# Main entry point for the Flask app
if __name__ == '__main__':
    app.run(debug=True)

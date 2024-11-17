# Import necessary modules
from flask import Flask, render_template, request, redirect, session, url_for, jsonify  # Flask framework components
import sqlite3  # SQLite database interface
from markupsafe import Markup  # HTML sanitization for safe HTML rendering
import hashlib  # For hashing passwords
from datetime import datetime  # For date calculations
from werkzeug.utils import secure_filename
import os

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'super secret key'  # Secret key for session management

    # Configure upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Define database path and dictionaries for vehicle makes and models
db_path = 'car_rental.db'
MAKES = {"": "Make"}
MODELS = {"": "Model"}

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

    return render_template("products.html", vehicle_html=vehicle_html, options=options)

# Route for displaying details of a specific vehicle
@app.route('/vehicle/<int:vehicle_id>')
def vehicle_page(vehicle_id):
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

    return render_template(
        'product.html',
        vehicleID=vehicle[0],
        year=vehicle[3],
        make=vehicle[1],
        model=vehicle[2],
        image_section=image_section,
        features_section=features_section,
        description_section=description_section,
        map_section=map_section
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
        session.clear()  # Clear session data
        return render_template("admin.html")
    else:
        return redirect(url_for("products"))

# Route for adding a vehicle to the cart
@app.route("/addToCart", methods=['POST'])
def addToCart():
    if "UserID" not in session:
        return redirect(url_for("index"))
    vehicle_id = request.form['vehicleID']
    daterange = request.form['daterange']
    
    # Store reservation details in session
    session["reservedCars"] += vehicle_id + "," + daterange + ";"
    
    return redirect(url_for("products"))

# Route for removing a vehicle from the cart
@app.route('/remove/<int:vehicle_id>')
def remove_from_cart(vehicle_id):
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if not session.get("reservedCars"):
        return redirect(url_for("products"))
    
    reservedCars = session["reservedCars"].strip().split(";")
    newReservedCars = ""
    
    for car in reservedCars:
        car = car.strip().split(",")
        if len(car) == 2 and car[0] != str(vehicle_id):
            newReservedCars += car[0] + "," + car[1] + ";"
    
    session["reservedCars"] = newReservedCars
    return redirect(url_for("cart"))

# Route to display cart contents
@app.route("/cart", methods=['POST', 'GET'])
def cart():
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if not session.get("reservedCars"):
        return render_template("shopping-cart.html", cart_html="Your cart is empty.")
    
    cart_html = ""
    reservedCars = session["reservedCars"].strip().split(";")
    
    for car in reservedCars:
        car = car.strip().split(",")
        if len(car) == 2:
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
                    <td class="border-0 align-middle"><a href="/remove/{VehicleID}" class="text-dark"><i class="fa fa-trash"></i></a></td>
                    </tr>"""
            ).format(Photo=vehicle[10].split("ㄹ")[0], year=vehicle[3], make=vehicle[1], model=vehicle[2], type=vehicle[4], dates=car[1], VehicleID=vehicle[0], numDays=getNumDays(car[1]))
            
    checkout_html, totalData = GetCheckoutValues(reservedCars)
            
    return render_template("shopping-cart.html", cart_html=cart_html, Rates=checkout_html, subtotal=totalData[0], tax=totalData[1], total=totalData[2] )


# Allowed extensions are already defined in the config
def allowed_file(filename):
    """
    Check if the file extension is allowed.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


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
        password = "defaultpassword"  # Dummy password

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


"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~METHODS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""

# Function to generate HTML for each vehicle in the listing
def generate_vehicle_html(vehicle_data):
    vehicle_html = ""
    
    # If no vehicles found, display "No Results Found" message
    if vehicle_data == []:
        vehicle_html = Markup(
            """
                <style>
                h1 {text-align: center; margin-top: 100px; margin-left: auto; margin-right: auto; width: 100%; font-size: 50px;}
                </style>
                <h1>No Results Found!</h1>
            """
        )
    
    # Iterate over vehicles, skipping if marked unavailable
    for vehicle in vehicle_data:
        if vehicle[9] == "no":
            continue

        # Generate HTML for each available vehicle
        vehicle_html += Markup(
            """<div class="col">
                 <div><a href="/vehicle/{VehicleID}"><img class="rounded img-fluid d-block w-100 fit-cover" style="height: 400px;width: 400px !important;" src="{photo}"></a>
                      <div class="py-4">
                          <h4>{year} {make} {model}</h4>
                      </div>
                 </div>
               </div>"""
        ).format(VehicleID=vehicle[0], photo=vehicle[10].split("ㄹ")[0], year=vehicle[3], make=vehicle[1], model=vehicle[2])

        # Add make and model to global dictionaries if not already present
        if vehicle[1] not in MAKES:
            MAKES[vehicle[1]] = vehicle[1]
        if vehicle[2] not in MODELS:
            MODELS[vehicle[2]] = vehicle[2]
    return vehicle_html

# Function to generate HTML options for filtering vehicle listings
def generate_options(selected_type, selected_make, selected_model, selected_drive, selected_transmission, selected_location, vehicle_data):
    """
    Generates HTML options with 'selected' attributes for each filter field based on current selections.
    """
    # Generate options for type filter
    type_options = generate_select_options(
        {"": "Type", "sedan": "Sedan", "suv": "SUV", "truck": "Truck", "coupe": "Coupe"},
        selected_type
    )
    
    # Generate options for make filter
    make_options = generate_select_options(
        MAKES,
        selected_make
    )
    
    # Generate options for model filter
    model_options = generate_select_options(
        MODELS,
        selected_model
    )
    
    # Generate options for drive type filter
    drive_options = generate_select_options(
        {"": "Drive Train", "4WD": "4x4", "FWD": "2x4", "AWD": "AWD"},
        selected_drive
    )
    
    # Generate options for transmission filter
    transmission_options = generate_select_options(
        {"": "Transmission", "manual": "Manual", "automatic": "Automatic"},
        selected_transmission
    )
    
    # Generate options for location filter
    location_options = generate_select_options(
        {"": "Location", "10": "123 Maple St", "11": "456 Oak Ave", "12": "789 Pine Dr"},
        selected_location
    )
    
    # Return all filter options as a dictionary
    return {
        'type_options': type_options,
        'make_options': make_options,
        'model_options': model_options,
        'drive_options': drive_options,
        'transmission_options': transmission_options,
        'location_options': location_options,
    }

# Extract unique makes from vehicle data
def get_unique_makes(vehicle_data):
    """
    Extracts unique makes from vehicle data.
    """
    makes = set(vehicle[1] for vehicle in vehicle_data)
    return sorted(makes)

# Helper function to generate <option> HTML elements for select inputs
def generate_select_options(options_dict, selected_value):
    """
    Helper function to generate HTML <option> elements with 'selected' attributes.
    """
    options_html = ""
    for value, label in options_dict.items():
        selected_attr = " selected" if value == selected_value else ""
        options_html += Markup("<option value='{value}'{selected}>{label}</option>").format(
            value=value, selected=selected_attr, label=label
        )
    return options_html

# Authenticate user and set session variables if credentials are correct
def login_user(email, password):
    data = get_user(email)
    try:
        # Check if hashed password matches database entry
        if data[10] == hashlib.sha3_512(password.encode()).hexdigest():
            # Set session data for user
            session["UserID"] = data[0]
            session["Name"] = data[1]
            session["Address"] = data[2]
            session["Phone"] = data[3]
            session["Email"] = data[4]
            session["Age"] = data[5]
            session["Gender"] = data[6]
            session["InsuranceCompany"] = data[7]
            session["UserPhoto"] = data[8]
            session["Username"] = data[9]
            session["DLPhotos"] = data[11]
            session["Usertype"] = data[12]
            session["reservedCars"] = ""
            
            # Log user type to console
            if data[12] == 0:
                print("Usertype: Regular User (0)")
            elif data[12] == 1:
                print("Usertype: Admin (1)")
            return(True, "")
        else:
            # Show error modal if password is incorrect
            modal = populateErrorModal("The password or email you have entered is incorrect")
            return (False, modal)
    except:
        # Handle errors with incorrect login details
        modal = populateErrorModal("The password or email you have entered is incorrect")
        return (False, modal)
            
# Function to populate an error modal with a specific message
def populateErrorModal(message, title="Oh No!"):
    modal = Markup("""
                    <div class="modal fade" role="dialog" id="errorModal">
                            <div class="modal-dialog modal-dialog-centered" role="document">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h4 class="modal-title">{title}</h4>
                                    </div>
                                    <div class="modal-body">
                                        <p>{message}</p>
                                    </div>
                                    <div class="modal-footer">
                                    <form>
                                        <button class="btn btn-light" type="button" data-bs-dismiss="modal" onclick="history.back()">Close</button>
                                    </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                    """).format(title=title, message=message)
    return modal

def check_password_meets_requirements(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    return True

def GetCheckoutValues(reservedCars):
    total = 0
    checkout_html = ""
    totalData = []
    types = []
    
    for car in reservedCars:
        car = car.strip().split(",")
        if len(car) == 2:
            vehicle = get_vehicle_by_id(car[0])
            rate = get_rates_by_vehicle_type(vehicle[4])[0]
            numDays = getNumDays(car[1])
            total += numDays * rate[3]
            if vehicle[4] not in types:
                types.append(vehicle[4])
                checkout_html += Markup("""
                                        <li class="d-flex justify-content-between py-3 border-bottom"><strong class="text-muted">{type} Rate </strong><strong>${rate:.2f}/day</strong></li>
                                        """).format(rate=rate[3], type=vehicle[4])
    totalData.append(f"{total:.2f}")
    totalData.append(f"{total * 0.07:.2f}")
    totalData.append(f"{float(totalData[0]) + float(totalData[1]):.2f}")
    return checkout_html, totalData

def getNumDays(dateRange):
    # dateRange format example "12/01/2024 - 12/15/2024"
    dates = dateRange.split(" - ")
    try:
        start_date = datetime.strptime(dates[0], "%m/%d/%Y")
        end_date = datetime.strptime(dates[1], "%m/%d/%Y")
    except ValueError:
        raise ValueError("Invalid date format. Please use MM/DD/YYYY - MM/DD/YYYY format.")
    
    # Calculate the number of days between the two dates
    delta = (end_date - start_date).days

    # Ensure the number of days is non-negative
    if delta < 0:
        raise ValueError("End date must be after start date.")
    
    return delta
    
"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~SQL QUERIES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""

# Retrieve user data by email from the database
def get_user(email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email=?", (email,))
    data = cursor.fetchone()
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

# Main entry point for the Flask app
if __name__ == '__main__':
    app.run(debug=True)
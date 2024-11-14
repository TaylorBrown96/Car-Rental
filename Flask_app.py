# Import necessary modules
from flask import Flask, render_template, request, redirect, session, url_for  # Flask framework components
import sqlite3  # SQLite database interface
from markupsafe import Markup  # HTML sanitization for safe HTML rendering
import hashlib  # For hashing passwords

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'super secret key'  # Secret key for session management

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

# Route to check and display reservation details
@app.route("/check_reservation", methods=['POST', 'GET'])
def check_reservation():
    if "UserID" not in session:
        return redirect(url_for("index"))
    
    if not session.get("reservedCars"):
        return redirect(url_for("products"))
    
    reservedCars = session["reservedCars"].strip().split(";")
    
    for car in reservedCars:
        car = car.strip().split(",")
        if len(car) == 2:
            print("Car ID: " + car[0] + " Date Range: " + car[1])
        else:
            print("Error: Unexpected format in reservedCars entry:", car)
    
    return redirect(url_for("products"))

# Route to clear all reservations from the session
@app.route("/clear_reservations", methods=['POST', 'GET'])
def clear_reservations():
    session["reservedCars"] = ""  # Clear reserved cars
    return redirect(url_for("products"))

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
                    <td class="border-0 align-middle"><a href="#" class="text-dark"><i class="fa fa-trash"></i></a></td>
                    </tr>"""
            ).format(Photo=vehicle[10].split("ㄹ")[0], year=vehicle[3], make=vehicle[1], model=vehicle[2], type=vehicle[4], dates=car[1], VehicleID=vehicle[0])
            
    return render_template("shopping-cart.html", cart_html=cart_html)




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

# Uncomment this route to test user creation; useful for initializing the database
"""
@app.route("/test")
def run_test():
    create_user("Taylor J. Brown", "123 ABC St. Fayetteville, NC 28314", 9168737714, "tbrown145@broncos.uncfsu.edu", 27, "M", "Test123abc")
    create_user("Admin", "123 ABC St. Fayetteville, NC 28314", 9105554545, "admin@admin.com", 99, "M", "Test123abc", 1)
    return redirect(url_for("index"))
"""

# Main entry point for the Flask app
if __name__ == '__main__':
    app.run(debug=True)
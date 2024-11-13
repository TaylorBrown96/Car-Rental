from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from markupsafe import Markup
import hashlib

app = Flask(__name__)
app.secret_key = 'super secret key'

# Path to the database file (The database used is SQLite and is stored in the same directory as the flask app).
db_path = 'car_rental.db'
MAKES = {"": "Make"}


@app.route("/")
def index():
    return render_template("login.html")

@app.route("/products", methods=['GET', 'POST'])
def products():
    if "UserID" not in session:
        return redirect(url_for("index"))

    # Store the selected values for each filter field
    selected_make = request.form.get('make', '') if request.method == 'POST' else ""
    selected_type = request.form.get('type', '') if request.method == 'POST' else ""
    selected_drive = request.form.get('drive', '') if request.method == 'POST' else ""
    selected_transmission = request.form.get('transmission', '') if request.method == 'POST' else ""
    selected_location = request.form.get('location', '') if request.method == 'POST' else ""
    
    # Retrieve vehicle data based on form inputs
    vehicle_data = (
        filter_vehicles(
            selected_type,
            selected_make,
            selected_drive,
            selected_transmission,
            selected_location
        ) if request.method == 'POST' else get_vehicle_information()
    )

    # Generate vehicle HTML and filter options
    vehicle_html = generate_vehicle_html(vehicle_data)
    options = generate_options(selected_make, selected_type, selected_drive, selected_transmission, selected_location, vehicle_data)

    return render_template("products.html", vehicle_html=vehicle_html, options=options)

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

@app.route("/logout", methods=['POST', 'GET'])
def logout():
    session.clear()
    return render_template("login.html")

@app.route("/signup", methods=['POST'])
def signup():
    return redirect(url_for("products"))


"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~METHODS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""
def generate_vehicle_html(vehicle_data):
    vehicle_html = ""
    
    if vehicle_data == []:
        vehicle_html = Markup(
            """
                <style>
                h1 {text-align: center; margin-top: 100px; margin-left: auto; margin-right: auto; width: 100%; font-size: 50px;}
                </style>

                <h1>No Results Found!</h1>
            """
        )
    
    for vehicle in vehicle_data:
        vehicle_html += Markup(
            """<div class="col" name="{VehicleID}">
                 <div><img class="rounded img-fluid d-block w-100 fit-cover" style="height: 400px;width: 400px !important;" src="{photo}">
                      <div class="py-4">
                          <h4>{year} {make} {model}</h4>
                      </div>
                 </div>
               </div>"""
        ).format(VehicleID=vehicle[0], photo=vehicle[10], year=vehicle[3], make=vehicle[1], model=vehicle[2])

        if vehicle[1] not in MAKES:
            MAKES[vehicle[1]] = vehicle[1]
    return vehicle_html

def generate_options(selected_make, selected_type, selected_drive, selected_transmission, selected_location, vehicle_data):
    """
    Generates HTML options with 'selected' attributes for each filter field based on current selections.
    """
    # Generate options for other fields
    type_options = generate_select_options(
        {"": "Type", "sedan": "Sedan", "suv": "SUV", "truck": "Truck", "coupe": "Coupe"},
        selected_type
    )
    
    make_options = generate_select_options(
        MAKES,
        selected_make
    )
    
    drive_options = generate_select_options(
        {"": "Drive Train", "fourWheel": "4x4", "twoWheel": "2x4", "allWheel": "AWD"},
        selected_drive
    )
    
    transmission_options = generate_select_options(
        {"": "Transmission", "manual": "Manual", "automatic": "Automatic"},
        selected_transmission
    )
    
    location_options = generate_select_options(
        {"": "Location", "location1": "Location1", "location2": "Location2", "location3": "Location3"},
        selected_location
    )
    
    return {
        'make_options': make_options,
        'type_options': type_options,
        'drive_options': drive_options,
        'transmission_options': transmission_options,
        'location_options': location_options,
    }

def get_unique_makes(vehicle_data):
    """
    Extracts unique makes from vehicle data.
    """
    makes = set(vehicle[1] for vehicle in vehicle_data)
    return sorted(makes)

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

def login_user(email, password):
    data = get_user(email)
    try:
        if data[10] == hashlib.sha3_512(password.encode()).hexdigest():
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
            
            # Flash Usertype to console
            if data[12] == 0:
                print("Usertype: Regular User (0)")
            elif data[12] == 1:
                print("Usertype: Admin (1)")
            return(True, "")
        else:
            modal = populateErrorModal("The password or email you have entered is incorrect")
            return (False, modal)
    except:
        modal = populateErrorModal("The password or email you have entered is incorrect")
        return (False, modal)
            
def populateErrorModal(message):
    modal = Markup("""
                    <div class="modal fade" role="dialog" id="errorModal">
                            <div class="modal-dialog modal-dialog-centered" role="document">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h4 class="modal-title">Oh No!</h4>
                                    </div>
                                    <div class="modal-body">
                                        <p>Message</p>
                                    </div>
                                    <div class="modal-footer">
                                    <form>
                                        <button class="btn btn-light" type="button" data-bs-dismiss="modal" onclick="history.back()">Close</button>
                                    </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                    """).replace("Message", message)
    return modal


"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~SQL QUERIES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""
def get_user(email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email=?", (email,))
    data = cursor.fetchone()
    conn.close()
    
    return data

def update_user(userID):
    pass

def create_user(name, address, phone, email, age, gender, password, userType=0):
    password = hashlib.sha3_512(password.encode()).hexdigest()
    username = email.split("@")[0]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Users (UserID, Name, Address, Phone, Email, Age, Gender, InsuranceCompany, UserPhoto, Username, Password, DLPhotos, Usertype) VALUES (NULL, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL, ?)", (name, address, phone, email, age, gender, username, password, userType, ))
    conn.commit()
    conn.close()

def filter_vehicles(type, make, drive, transmission, location):
    if type == "":
        type = "%"
    if make == "":
        make = "%"
    if drive == "":
        drive = "%"
    if transmission == "":
        transmission = "%"
    if location == "":
        location = "%"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicles WHERE Type LIKE ? AND Make LIKE ? AND Transmission LIKE ? AND LocationID LIKE ?", (type, make, transmission, location))
    data = cursor.fetchall()
    conn.close()
    
    return data

def get_vehicle_information():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicles")
    data = cursor.fetchall()
    conn.close()
    
    return data

def update_vehicle_information(vehicleID):
    pass


# Uncomment the docstring only when you specifically want to load users into database
"""@app.route("/test")
def run_test():
    create_user("Taylor J. Brown", "123 ABC St. Fayetteville, NC 28314", 9168737714, "tbrown145@broncos.uncfsu.edu", 27, "M", "Test123abc")
    create_user("Admin", "123 ABC St. Fayetteville, NC 28314", 9105554545, "admin@admin.com", 99, "M", "Test123abc", 1)
    return redirect(url_for("index"))"""

if __name__ == '__main__':
    app.run(debug=True)
    
import hashlib
from datetime import datetime, timedelta
from flask import session
from markupsafe import Markup
from sqlQueries import *


MAKES = {"": "Make"}
MODELS = {"": "Model"}


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
        if len(car) == 3:
            vehicle = get_vehicle_by_id(car[0])
            rate = get_rates_by_vehicle_type(vehicle[4])[0]
            numDays = getNumDays(car[1])
            total += numDays * rate[3]
            if vehicle[4] not in types:
                types.append(vehicle[4])
                checkout_html += Markup("""
                                        <li class="d-flex justify-content-between py-3 border-bottom"><strong class="text-muted">{type} Rate </strong><strong>${rate:.2f}/day</strong></li>
                                        """).format(rate=rate[3], type=vehicle[4])
    totalData.append(f"{total + 30.00:.2f}")
    totalData.append(f"{float(totalData[0]) * 0.07:.2f}")
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


def generate_dates_between(start_date, end_date):
    # Parse the input dates from strings to datetime objects
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Generate a list of dates from start to end (inclusive)
    date_list = []
    current_date = start
    while current_date <= end:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    return date_list


def admin_nav():
    admin_html = Markup("""
                        <a href="/admin">
                            <button class="btn btn-primary shadow" type="button" data-bs-target="#signup" data-bs-toggle="modal" style="margin-right: 10px;">Admin Panel</button>
                        </a>""")
    return admin_html
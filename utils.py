# ---------------------- Imports and Constants ----------------------
import hashlib
from datetime import datetime, timedelta
from flask import session
from markupsafe import Markup
from sqlQueries import *

MAKES = {"": "Make"}
MODELS = {"": "Model"}

# ---------------------- HTML Generators ----------------------

def generate_vehicle_html(vehicle_data):
    """
    Generates HTML for vehicle listings.
    """
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
        if vehicle[9] == "no":
            continue
        vehicle_html += Markup(
            """<div class="col">
                 <div><a href="/vehicle/{VehicleID}">
                     <img class="rounded img-fluid d-block w-100 fit-cover" style="height: 400px;width: 400px !important;" src="{photo}"></a>
                     <div class="py-4">
                         <h4>{year} {make} {model}</h4>
                     </div>
                 </div>
               </div>"""
        ).format(VehicleID=vehicle[0], photo=vehicle[10].split("ㄹ")[0], year=vehicle[3], make=vehicle[1], model=vehicle[2])
        if vehicle[1] not in MAKES:
            MAKES[vehicle[1]] = vehicle[1]
        if vehicle[2] not in MODELS:
            MODELS[vehicle[2]] = vehicle[2]
    return vehicle_html

def generate_options(selected_type, selected_make, selected_model, selected_drive, selected_transmission, selected_location, vehicle_data):
    """
    Generates HTML options with 'selected' attributes for filter fields.
    """
    type_options = generate_select_options(
        {"": "Type", "sedan": "Sedan", "suv": "SUV", "truck": "Truck", "coupe": "Coupe"},
        selected_type
    )
    make_options = generate_select_options(MAKES, selected_make)
    model_options = generate_select_options(MODELS, selected_model)
    drive_options = generate_select_options(
        {"": "Drive Train", "4WD": "4x4", "FWD": "2x4", "AWD": "AWD"},
        selected_drive
    )
    transmission_options = generate_select_options(
        {"": "Transmission", "manual": "Manual", "automatic": "Automatic"},
        selected_transmission
    )
    location_options = generate_select_options(
        {"": "Location", "10": "123 Maple St", "11": "456 Oak Ave", "12": "789 Pine Dr"},
        selected_location
    )
    return {
        'type_options': type_options,
        'make_options': make_options,
        'model_options': model_options,
        'drive_options': drive_options,
        'transmission_options': transmission_options,
        'location_options': location_options,
    }

def generate_cart_html(reserved_cars):
    """
    Generates the HTML content for the cart table.
    """
    cart_html = ""
    for car in reserved_cars:
        car_details = car.strip().split(",")
        if len(car_details) == 3:
            vehicle_id = car_details[0]
            date_range = car_details[1]
            reserve_id = car_details[2]
            vehicle = get_vehicle_by_id(vehicle_id)
            if vehicle:
                cart_html += Markup(
                    """<tr>
                        <th scope="row" class="border-0">
                            <div class="p-2">
                                <img src="{Photo}" alt="" width="70" class="img-fluid rounded shadow-sm">
                                <div class="ml-3 d-inline-block align-middle">
                                    <h5 class="mb-0"> 
                                        <a href="/vehicle/{VehicleID}" class="text-dark d-inline-block align-middle">
                                            {year} {make} {model}
                                        </a>
                                    </h5>
                                    <span class="text-muted font-weight-normal font-italic d-block">Type: {type}</span>
                                </div>
                            </div>
                        </th>
                        <td class="border-0 align-middle"><strong>{dates}</strong></td>
                        <td class="border-0 align-middle"><strong>{numDays}</strong></td>
                        <td class="border-0 align-middle">
                            <a href="/remove/{ReserveID}" class="text-dark">
                                <i class="fa fa-trash"></i>
                            </a>
                        </td>
                    </tr>"""
                ).format(
                    Photo=vehicle[10].split("ㄹ")[0],
                    year=vehicle[3],
                    make=vehicle[1],
                    model=vehicle[2],
                    type=vehicle[4],
                    dates=date_range,
                    VehicleID=vehicle_id,
                    numDays=getNumDays(date_range) + 1,
                    ReserveID=reserve_id
                )
    return cart_html

# ---------------------- Utilities ----------------------

def generate_select_options(options_dict, selected_value):
    """
    Helper function to generate HTML <option> elements.
    """
    options_html = ""
    for value, label in options_dict.items():
        selected_attr = " selected" if value == selected_value else ""
        options_html += Markup("<option value='{value}'{selected}>{label}</option>").format(
            value=value, selected=selected_attr, label=label
        )
    return options_html

def generate_dates_between(start_date, end_date):
    """
    Generates a list of dates between start and end dates.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_list = []
    current_date = start
    while current_date <= end:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    return date_list

# ---------------------- Authentication and User Management ----------------------

def login_user(email, password):
    data = get_user(email)
    if data == None:
        modal = populateErrorModal("The password or email you have entered is incorrect")
        return (False, modal)
    
    if data[13] == 'False':
        modal = populateErrorModal("Your account has been disabled. Please contact an administrator for assistance.", title="Account Disabled")
        return (False, modal)
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

def check_password_meets_requirements(password):
    """
    Checks if the password meets basic security requirements.
    """
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    return True

# ---------------------- Vehicle Operations ----------------------

def get_price_by_vehicleid(vehicleID, numDays):
    """
    Calculates the price for a vehicle rental based on its type and number of days.
    """
    rate = get_rates_by_vehicle_type(get_vehicle_by_id(vehicleID)[4])[0]
    return (rate[3] * numDays + 30.00) * 1.07

# ---------------------- Reservation Operations ----------------------

def GetCheckoutValues(reservedCars):
    """
    Calculates checkout totals and generates HTML for selected vehicles.
    """
    total = 0
    checkout_html = ""
    totalData = []
    types = []
    for car in reservedCars:
        car = car.strip().split(",")
        if len(car) == 3:
            vehicle = get_vehicle_by_id(car[0])
            rate = get_rates_by_vehicle_type(vehicle[4])[0]
            numDays = getNumDays(car[1]) + 1
            total += numDays * rate[3]
            if vehicle[4] not in types:
                types.append(vehicle[4])
                checkout_html += Markup(
                    """<li class="d-flex justify-content-between py-3 border-bottom">
                       <strong class="text-muted">{type} Rate </strong><strong>${rate:.2f}/day</strong></li>"""
                ).format(rate=rate[3], type=vehicle[4])
    totalData.append(f"{total + 30.00:.2f}")
    totalData.append(f"{float(totalData[0]) * 0.07:.2f}")
    totalData.append(f"{float(totalData[0]) + float(totalData[1]):.2f}")
    return checkout_html, totalData

def getNumDays(dateRange):
    """
    Calculates the number of days in a given date range.
    """
    dates = dateRange.split(" - ")
    try:
        start_date = datetime.strptime(dates[0], "%m/%d/%Y")
        end_date = datetime.strptime(dates[1], "%m/%d/%Y")
    except ValueError:
        raise ValueError("Invalid date format. Please use MM/DD/YYYY - MM/DD/YYYY format.")
    delta = (end_date - start_date).days
    if delta < 0:
        raise ValueError("End date must be after start date.")
    return delta

def generate_pickupdropoff_html(reservationsTableData):
    """
    Generates HTML for pickup and drop-off reservation tables.
    """
    html = ""
    for reservation in reservationsTableData:
        html += Markup(
            """
            <tr>
                <td class="text-truncate" style="max-width: 200px;">{ReservationID}</td>
                <td class="text-truncate" style="max-width: 200px;">{VehicleID}</td>
                <td>{InvoiceID}</td>
                <td class="text-truncate" style="max-width: 200px;">{Email}</td>
                <td class="text-truncate" style="max-width: 200px;">{ReserveStartDate}</td>
                <td class="text-truncate" style="max-width: 200px;">{ReserveEndDate}</td>
                <td class="text-center">
                    <button data-bs-target="#modal-{ReservationID}" type="button" data-bs-toggle="modal" 
                            style="border:none; background: none;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="currentColor" 
                             viewBox="0 0 16 16" class="bi bi-eye-fill fs-5 text-primary">
                            <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0"></path>
                            <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8m8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7"></path>
                        </svg>
                    </button>
                </td>
            </tr>
            """
        ).format(
            ReservationID=reservation[0],
            VehicleID=reservation[1],
            InvoiceID=reservation[4],
            Email=reservation[7],
            ReserveStartDate=reservation[2],
            ReserveEndDate=reservation[3]
        )
    return html

def pickup_modal_html(ReservationID):
    reservation_data = get_reservation_by_id(ReservationID)
    vehicle_data = get_vehicle_by_id(reservation_data[1])
    pickuploc = get_location_by_id(reservation_data[10])[1]
    dropoffloc = get_location_by_id(reservation_data[11])[1]
    pickup_html = Markup("""
        <div class="modal fade" role="dialog" tabindex="-1" id="modal-{ReservationID}">
            <div class="modal-dialog modal-xl" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4 class="modal-title">Customer Pickup</h4><button class="btn-close" type="button" aria-label="Close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="container">
                            <div class="row">
                                <div class="col-md-6">
                                    <h1 style="margin-bottom: 15px;">Vehicle Data:</h1>
                                    <p>Make:&nbsp;{Make}</p>
                                    <p>Model:&nbsp;{Model}</p>
                                    <p>Year:&nbsp;{Year}</p>
                                    <p>Type:&nbsp;{Type}</p>
                                    <p>Mileage:&nbsp;{Mileage}</p>
                                    <p>Transmission:&nbsp;{Trans}</p>
                                    <p>Drive Train:&nbsp;{Drive}</p>
                                </div>
                                <div class="col-md-6">
                                    <h1 style="margin-bottom: 15px;">Reservation Data:</h1>
                                    <p>Start Date:&nbsp;{ReservationStart}</p>
                                    <p>End Date:&nbsp;{ReservationEnd}</p>
                                    <p>Pickup Location:&nbsp;{pickuploc}</p>
                                    <p>Drop Off Location:&nbsp;{dropoffloc}</p>
                                    <p style="margin-bottom: 30px;">Estimated Total:&nbsp;{estTotal}</p>""").format(Make=vehicle_data[1], Model=vehicle_data[2], Year=vehicle_data[3], Type=vehicle_data[4], Mileage=vehicle_data[5], Trans=vehicle_data[6], Drive=vehicle_data[15], 
                                          ReservationID=ReservationID, ReservationStart=reservation_data[6], ReservationEnd=reservation_data[7], estTotal="%0.2f" % (reservation_data[15]), pickuploc=pickuploc, dropoffloc=dropoffloc)
                                    
    if reservation_data[4] == "False":                                
        pickup_html += Markup("""<p>Signed Rental Agreement Status:&nbsp;<label style="color: Red; font-size: 2rem;">&nbsp;&nbsp;Not Signed</label></p>
                              </div>
                            </div>
                        </div>
                        <form style="margin-top: 20px;margin-bottom: 20px;" action="/uploadRentalAgreement/{ReservationID}" method="POST" enctype="multipart/form-data">
                            <div class="container">
                                <div class="row">
                                    <div class="col-md-4" style="width: 32%;"><label class="col-form-label" style="font-weight: bold;font-size: 20px;">Upload Signed Rental Agreement</label></div>
                                    <div class="col-md-4" style="width: 43%;"><input class="form-control" type="file" name="rentalAgreement"></div>
                                    <div class="col-md-4" style="width: 25%;"><button class="btn btn-primary" type="submit">Upload Document</button></div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer"><a style="color: white;" href="/GenerateRentalAgreement/{ReservationID}"><button class="btn btn-primary" type="button" data-bs-dismiss="modal" style="margin-right: 43%;">Generate Rental Agreement</a></button><button class="btn btn-light" type="button" data-bs-dismiss="modal">Cancel</button><button class="btn btn-light" type="button" disabled>Confirm Pickup</button></div>
                </div>
            </div>
        </div>""").format(ReservationID=ReservationID)
    else:
       pickup_html += Markup("""<p>Signed Rental Agreement Status:&nbsp;<label style="color: Green; font-size: 2rem;">&nbsp;&nbsp;Signed</label></p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer"><button class="btn btn-light" type="button" data-bs-dismiss="modal">Cancel</button><a href="/pickup/{ReservationID}" style"color:white;"><button class="btn btn-success" type="button">Confirm Pickup</button></a></div>
                </div>
            </div>
        </div>""").format(ReservationID=ReservationID) 

    return pickup_html


def dropoff_modal_html(ReservationID):
    reservation_data = get_reservation_by_id(ReservationID)
    vehicle_data = get_vehicle_by_id(reservation_data[1])
    paymentStatus = get_payment_status(ReservationID)
    pickuploc = get_location_by_id(reservation_data[10])[1]
    dropoffloc = get_location_by_id(reservation_data[11])[1]
    
    dropoff_html = Markup("""<div class="modal fade" role="dialog" tabindex="-1" id="modal-{ReservationID}">
            <div class="modal-dialog modal-xl" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4 class="modal-title">Customer Drop Off</h4><button class="btn-close" type="button" aria-label="Close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="container">
                            <div class="row">
                                <div class="col-md-6">
                                    <h1 style="margin-bottom: 15px;">Vehicle Data:</h1>
                                    <p>Make:&nbsp;{Make}</p>
                                    <p>Model:&nbsp;{Model}</p>
                                    <p>Year:&nbsp;{Year}</p>
                                    <p>Type:&nbsp;{Type}</p>
                                    <p>Mileage:&nbsp;{Mileage}</p>
                                    <p>Transmission:&nbsp{Trans}</p>
                                    <p>Drive Train:&nbsp;{Drive}</p>
                                </div>
                                <div class="col-md-6">
                                    <h1 style="margin-bottom: 15px;">Reservation Data:</h1>
                                    <p>Start Date:&nbsp;{ReservationStart}</p>
                                    <p>End Date:&nbsp;{ReservationEnd}</p>
                                    <p>Pickup Location:&nbsp;{pickuploc}</p>
                                    <p>Drop Off Location:&nbsp;{dropoffloc}</p>
                                    <p style="margin-bottom: 60px;">Estimated Total:&nbsp;{estTotal}</p>
                                    <p>Payment Status:&nbsp;{paymentStatus}
                                """).format(Make=vehicle_data[1], Model=vehicle_data[2], Year=vehicle_data[3], Type=vehicle_data[4], Mileage=vehicle_data[5], Trans=vehicle_data[6], Drive=vehicle_data[15], 
                                          ReservationID=ReservationID, ReservationStart=reservation_data[6], ReservationEnd=reservation_data[7], estTotal="%0.2f" % (reservation_data[15]), paymentStatus=paymentStatus, pickuploc=pickuploc, dropoffloc=dropoffloc)
                        
    if paymentStatus == "none" or paymentStatus == "Partial":
        dropoff_html += Markup("""&nbsp;&nbsp;{AmountPaid}</p>
                                </div>
                            </div>
                        </div>
                        <form style="margin-top: 20px; margin-bottom: 20px;" method="POST" action="/updateReservation/{ReservationID}">
                            <input class="form-control" type="number" placeholder="Payment Amount" style="margin-bottom: 15px;" inputmode="decimal" name="paymentamount" step=".01" required>
                            <input class="form-control" type="number" placeholder="Returning Mileage" name="mileage" min="0" required>
                            <button class="btn btn-primary" type="submit" style="margin-top: 15px;">Submit Vehicle Data</button>
                            <a href="/generateRentalBill/{ReservationID}"><button class="btn btn-warning" type="button" data-bs-dismiss="modal" style="margin-left: 1%; margin-top: 15px;">Generate Rental Bill</button></a>
                        </form>
                    </div>
                </div>
            </div>
        </div>""").format(ReservationID=ReservationID, AmountPaid= f"Amount Paid: ${float(get_invoice_PaidAmount(ReservationID)):.2f}  Remaining: ${float(reservation_data[15]) - float(get_invoice_PaidAmount(ReservationID)):.2f}")
    else:
        dropoff_html += Markup("""</p>
                                </div>
                            </div>
                        </div>    
                    </div>
                    <div class="modal-footer">
                        <a href="/generateConsolidatedRentalBill/{ReservationID}"><button class="btn btn-warning" type="button" data-bs-dismiss="modal" style="margin-right: 0%;">Generate Consolidated Rental Bill</button></a>
                        <button class="btn btn-light" type="button" data-bs-dismiss="modal">Cancel</button>
                        <a href="/dropoff/{ReservationID}"><button class="btn btn-success" type="button">Confirm Drop Off</button></a>
                    </div>
                </div>
            </div>
        </div>""").format(ReservationID=ReservationID)
        

    return dropoff_html

# ---------------------- Admin and Navigation Utilities ----------------------

def admin_nav():
    """
    Generates HTML for the admin navigation button.
    """
    admin_html = Markup(
        """
        <a href="/admin">
            <button class="btn btn-primary shadow" type="button" style="margin-right: 10px;">Admin Panel</button>
        </a>
        """
    )
    return admin_html

def generate_location_options(locationOptions):
    """
    Generates HTML for location options in select input fields.
    """
    locationOptions_html = ""
    for location in locationOptions:
        locationOptions_html += Markup(
            """<option value="{LocationID}">{LocationName}</option>"""
        ).format(LocationID=location[0], LocationName=location[1])
    return locationOptions_html

# ---------------------- Error Handling and Modals ----------------------

def populateErrorModal(message, title="Oh No!"):
    """
    Generates HTML for an error modal with a specified message and title.
    """
    modal = Markup(
        """
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
        """
    ).format(title=title, message=message)
    return modal
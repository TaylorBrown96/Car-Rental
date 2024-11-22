from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import sqlite3
from utils import *
from io import BytesIO


def vehicleReport(start_date, end_date):
    conn = sqlite3.connect("car_rental.db")
    cursor = conn.cursor()

    # Query for cars rented within the date range
    cursor.execute("""
        SELECT 
            v.VehicleID, 
            v.Year || ' ' || v.Make || ' ' || v.Model AS Name, 
            r.ReserveStartDate, 
            r.ReserveEndDate
        FROM Reservations r
        JOIN Vehicles v ON r.VehicleID = v.VehicleID
        WHERE DATE(STRFTIME('%Y-%m-%d', SUBSTR(r.ReserveStartDate, 7, 4) || '-' || 
                                        SUBSTR(r.ReserveStartDate, 1, 2) || '-' || 
                                        SUBSTR(r.ReserveStartDate, 4, 2))) <= ? 
        AND DATE(STRFTIME('%Y-%m-%d', SUBSTR(r.ReserveEndDate, 7, 4) || '-' || 
                                        SUBSTR(r.ReserveEndDate, 1, 2) || '-' || 
                                        SUBSTR(r.ReserveEndDate, 4, 2))) >= ?
    """, (end_date, start_date))
    rented_cars = cursor.fetchall()

    # Query for cars in-house
    cursor.execute("""
        SELECT VehicleID, v.Year || ' ' || v.Make || ' ' || v.Model AS Name 
        FROM Vehicles v
        WHERE Available = 'Yes'
    """)
    in_house_cars = cursor.fetchall()

    # Query for revenue within the date range
    cursor.execute("""
        SELECT SUM(r.TotalPrice) AS Revenue
        FROM Reservations r
        WHERE DATE(STRFTIME('%Y-%m-%d', SUBSTR(r.ReserveStartDate, 7, 4) || '-' || 
                                            SUBSTR(r.ReserveStartDate, 1, 2) || '-' || 
                                            SUBSTR(r.ReserveStartDate, 4, 2))) <= ? 
        AND DATE(STRFTIME('%Y-%m-%d', SUBSTR(r.ReserveEndDate, 7, 4) || '-' || 
                                            SUBSTR(r.ReserveEndDate, 1, 2) || '-' || 
                                            SUBSTR(r.ReserveEndDate, 4, 2))) >= ?
    """, (end_date, start_date))
    revenue = cursor.fetchone()[0] or 0.0

    # Query for unavailable cars without reservations within the date range
    cursor.execute("""
        SELECT v.VehicleID, v.Year || ' ' || v.Make || ' ' || v.Model AS Name
        FROM Vehicles v
        WHERE v.Available = 'No'
        AND v.VehicleID NOT IN (
            SELECT r.VehicleID
            FROM Reservations r
            WHERE DATE(STRFTIME('%Y-%m-%d', SUBSTR(r.ReserveStartDate, 7, 4) || '-' || 
                                            SUBSTR(r.ReserveStartDate, 1, 2) || '-' || 
                                            SUBSTR(r.ReserveStartDate, 4, 2))) <= ? 
            AND DATE(STRFTIME('%Y-%m-%d', SUBSTR(r.ReserveEndDate, 7, 4) || '-' || 
                                            SUBSTR(r.ReserveEndDate, 1, 2) || '-' || 
                                            SUBSTR(r.ReserveEndDate, 4, 2))) >= ?
        )
    """, (end_date, start_date))
    unavailable_cars = cursor.fetchall()

    conn.close()

    # Generate the PDF
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)

    current_date = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 750, "Car Rental Report")
    pdf.drawString(50, 735, f"Generated on: {current_date.replace('_', ' at ')}")
    pdf.drawString(50, 720, f"Report Range: {start_date} to {end_date}")

    y = 700
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Cars Currently Rented:")
    y -= 15
    pdf.setFont("Helvetica", 12)
    for car in rented_cars:
        pdf.drawString(50, y, f"Vehicle ID: {car[0]}, Name: {car[1]}, Rented From: {car[2]} - {car[3]}")
        y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Cars In-House/Available For Rent:")
    y -= 15
    pdf.setFont("Helvetica", 12)
    for car in in_house_cars:
        pdf.drawString(50, y, f"Vehicle ID: {car[0]}, Name: {car[1]}")
        y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Total Revenue Earned:")
    y -= 15
    pdf.setFont("Helvetica", 12)
    pdf.drawString(200, y, f"${revenue:.2f}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Unavailable Cars Without Current Reservations:")
    y -= 15
    pdf.setFont("Helvetica", 12)
    for car in unavailable_cars:
        pdf.drawString(50, y, f"Vehicle ID: {car[0]}, Name: {car[1]}")
        y -= 15

    pdf.save()
    pdf_buffer.seek(0)

    response = make_response(pdf_buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=vehicle_report_{start_date}_to_{end_date}.pdf"

    return response


def draw_wrapped_text(pdf, text, x, y, width=400, line_height=12):
    """Helper function to draw wrapped text."""
    lines = simpleSplit(text, "Helvetica", 12, width)
    for line in lines:
        pdf.drawString(x, y, line)
        y -= line_height
    return y  # Return the new y-coordinate after wrapping

def rentalAgreement(reservation_id):
    conn = sqlite3.connect("car_rental.db")
    cursor = conn.cursor()

    # Fetch reservation details
    cursor.execute("""
        SELECT r.ReservationID, r.VehicleID, r.UserID, r.PlanID, r.ReserveStartDate, 
                r.ReserveEndDate, r.PickUpLocation, r.DropOffLocation, r.InvoiceID, 
                v.Make, v.Model, v.Year, v.Type, v.Mileage, v.Transmission, v.NumDoors, 
                v.DriveTrain, v.Description
        FROM Reservations r
        JOIN Vehicles v ON r.VehicleID = v.VehicleID
        WHERE r.ReservationID = ?
    """, (reservation_id,))
    reservation = cursor.fetchone()

    # Fetch pickup and dropoff location details
    cursor.execute("SELECT Address, Phone FROM Locations WHERE LocationID = ?", (reservation[6],))
    pickup_details = cursor.fetchone()
    pickup_address, pickup_phone = pickup_details[0], pickup_details[1]

    cursor.execute("SELECT Address, Phone FROM Locations WHERE LocationID = ?", (reservation[7],))
    dropoff_details = cursor.fetchone()
    dropoff_address, dropoff_phone = dropoff_details[0], dropoff_details[1]
    
    conn.close()

    # Generate the PDF in-memory
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Rental Agreement")

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(250, 750, "Rental Agreement")

    # Reservation and Vehicle Details
    y = 710
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Reservation and Vehicle Details:")
    y -= 20

    def add_bold_descriptor(label, value):
        nonlocal y
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, label)
        pdf.setFont("Helvetica", 12)
        pdf.drawString(200, y, value)
        y -= 20
        
    pdf.setFont("Helvetica-Bold", 12)
    add_bold_descriptor("Reservation ID:", str(reservation[0]))
    add_bold_descriptor("Vehicle:", f"{reservation[9]} {reservation[10]} ({reservation[11]})")
    add_bold_descriptor("Type:", reservation[12])
    add_bold_descriptor("Mileage:", f"{reservation[13]} miles")
    add_bold_descriptor("Transmission:", reservation[14])
    add_bold_descriptor("Doors:", str(reservation[15]))
    add_bold_descriptor("DriveTrain:", reservation[16])

    pdf.setFont("Helvetica-Bold", 12)
    y = draw_wrapped_text(pdf, f"Description:", 50, y, line_height=16)
    pdf.setFont("Helvetica", 12)
    y -= 10
    y = draw_wrapped_text(pdf, reservation[17], 100, y)

    # Rental Dates
    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Rental Dates:")
    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    add_bold_descriptor("Start:", reservation[4])
    add_bold_descriptor("Pickup Location:", pickup_address)
    add_bold_descriptor("Phone:", pickup_phone)
    y -= 20
    add_bold_descriptor("End:", reservation[5])
    add_bold_descriptor("Dropoff Location:", dropoff_address)
    add_bold_descriptor("Phone:", dropoff_phone)

    # Billing Information
    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Billing Information:")
    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    add_bold_descriptor("Invoice ID:", str(reservation[8]))


    # Signature Block (sticky bottom)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(70, 130, "Customer Signature: ________________________")
    pdf.drawString(350, 130, "Date: _______________")
    y -= 10
    pdf.drawString(70, 110, "Agent Signature:    __________________________")
    pdf.drawString(350, 110, "Date: _______________")

    # Save the PDF
    pdf.save()
    buffer.seek(0)

    # Create a Flask response
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=rental_agreement_{reservation_id}.pdf'
    
    return response


def invoiceFromReservation(reservation_id):
    conn = sqlite3.connect("car_rental.db")
    cursor = conn.cursor()

    # Step 1: Find the CustomerID for the given ReservationID
    cursor.execute("""
        SELECT CustomerID 
        FROM Reservations
        WHERE ReservationID = ?
    """, (reservation_id,))
    customer_data = cursor.fetchone()

    if not customer_data:
        conn.close()
        return "Reservation not found.", 404

    customer_id = customer_data[0]

    # Step 2: Fetch all reservations for the CustomerID, including paid amounts
    cursor.execute("""
        SELECT r.ReservationID, r.VehicleID, r.UserID, r.PlanID, r.ReserveStartDate,
               r.ReserveEndDate, r.PickUpLocation, r.DropOffLocation, r.NumDays,
               rp.Name, rp.Type, rp.Rate, v.Year || ' ' || v.Make || ' ' || v.Model AS VehicleName,
               i.PaidAmount
        FROM Reservations r
        JOIN RentalPlans rp ON r.PlanID = rp.PlanID
        JOIN Vehicles v ON r.VehicleID = v.VehicleID
        JOIN Invoice i ON r.ReservationID = i.ReservationID
        WHERE r.CustomerID = ?
    """, (customer_id,))
    reservations = cursor.fetchall()

    conn.close()

    if not reservations:
        return "No reservations found for the customer.", 404

    # Step 3: Calculate totals and prepare data for the PDF
    subtotal = 0
    admin_fee = 0
    total_paid = 0
    reservations_data = []

    for reservation in reservations:
        (reservation_id, vehicle_id, user_id, plan_id, reserve_start_date, reserve_end_date,
         pickup_location, dropoff_location, num_days, plan_name, plan_type, rate, vehicle_name, paid_amount) = reservation

        total_price = round(num_days * rate, 2)  # Pre-tax total for this vehicle
        subtotal += total_price
        total_paid += float(paid_amount) if paid_amount else 0.0  # Sum paid amounts
        reservations_data.append({
            "Vehicle": vehicle_name,
            "Start": reserve_start_date,
            "End": reserve_end_date,
            "Days": num_days,
            "Rate": rate,
            "TotalPrice": total_price,
            "PaidAmount": float(paid_amount) if paid_amount else 0.0,
            "Pickup": pickup_location,
            "Dropoff": dropoff_location
        })
        admin_fee += 30.00  # Admin fee per vehicle

    # Calculate tax and total
    tax = round(subtotal * 0.07, 2)
    total = round(subtotal + admin_fee + tax, 2)
    remaining_balance = round(total - total_paid, 2)

    # Step 4: Generate the PDF
    return generatePDF(
        customer_id=customer_id,
        reservations_data=reservations_data,
        subtotal=subtotal,
        admin_fee=admin_fee,
        tax=tax,
        total=total,
        total_paid=total_paid,
        remaining_balance=remaining_balance,
        title="Consolidated Invoice"
    )


def invoiceForSingleVehicle(reservation_id):
    conn = sqlite3.connect("car_rental.db")
    cursor = conn.cursor()

    # Step 1: Fetch reservation details for the given ReservationID, including paid amount
    cursor.execute("""
        SELECT r.ReservationID, r.VehicleID, r.UserID, r.PlanID, r.ReserveStartDate,
               r.ReserveEndDate, r.PickUpLocation, r.DropOffLocation, r.NumDays,
               rp.Name, rp.Type, rp.Rate, v.Year || ' ' || v.Make || ' ' || v.Model AS VehicleName,
               i.PaidAmount
        FROM Reservations r
        JOIN RentalPlans rp ON r.PlanID = rp.PlanID
        JOIN Vehicles v ON r.VehicleID = v.VehicleID
        JOIN Invoice i ON r.ReservationID = i.ReservationID
        WHERE r.ReservationID = ?
    """, (reservation_id,))
    reservation = cursor.fetchone()

    conn.close()

    if not reservation:
        return "Reservation not found.", 404

    # Extract reservation details
    (reservation_id, vehicle_id, user_id, plan_id, reserve_start_date, reserve_end_date,
     pickup_location, dropoff_location, num_days, plan_name, plan_type, rate, vehicle_name, paid_amount) = reservation

    # Calculate totals for the single vehicle
    total_price = round(num_days * rate, 2)
    admin_fee = 30.00
    tax = round((total_price+admin_fee) * 0.07, 2)
    total = round(total_price + admin_fee + tax, 2)
    total_paid = float(paid_amount) if paid_amount else 0.0
    remaining_balance = round(total - total_paid, 2)

    # Prepare data for the PDF
    reservations_data = [{
        "Vehicle": vehicle_name,
        "Start": reserve_start_date,
        "End": reserve_end_date,
        "Days": num_days,
        "Rate": rate,
        "TotalPrice": total_price,
        "PaidAmount": total_paid,
        "Pickup": pickup_location,
        "Dropoff": dropoff_location
    }]

    # Generate the PDF
    return generatePDF(
        customer_id=user_id,
        reservations_data=reservations_data,
        subtotal=total_price,
        admin_fee=admin_fee,
        tax=tax,
        total=total,
        total_paid=total_paid,
        remaining_balance=remaining_balance,
        title="Single Vehicle Invoice"
    )


def generatePDF(customer_id, reservations_data, subtotal, admin_fee, tax, total, total_paid, remaining_balance, title):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"{title} - Customer #{customer_id}")

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 750, f"{title} for Customer #{customer_id}")

    # Table Headers
    y = 720
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Vehicle")
    pdf.drawString(200, y, "Start Date")
    pdf.drawString(300, y, "End Date")
    pdf.drawString(400, y, "Days")
    pdf.drawString(450, y, "Rate/Day")
    pdf.drawString(520, y, "Total")
    y -= 20

    # Table Rows
    pdf.setFont("Helvetica", 12)
    for data in reservations_data:
        pdf.drawString(50, y, data["Vehicle"])
        pdf.drawString(200, y, data["Start"])
        pdf.drawString(300, y, data["End"])
        pdf.drawString(400, y, str(data["Days"]))
        pdf.drawString(450, y, f"${data['Rate']:.2f}")
        pdf.drawString(520, y, f"${data['TotalPrice']:.2f}")
        y -= 15

        if y < 100:  # Add new page if needed
            pdf.showPage()
            y = 750

    # Add totals section
    y -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "_" * 80)  # Separator line
    y -= 20

    pdf.drawString(400, y, "Subtotal:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(520, y, f"${subtotal:.2f}")
    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, y, "Admin Fee:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(520, y, f"${admin_fee:.2f}")
    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, y, "Tax (NC 7.00%):")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(520, y, f"${tax:.2f}")
    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, y, "Total:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(520, y, f"${total:.2f}")
    y -= 20

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, y, "Amount Paid:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(520, y, f"${total_paid:.2f}")
    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, y, "Remaining Balance:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(520, y, f"${remaining_balance:.2f}")
    y -= 20

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "_" * 80)  # Separator line

    # Footer
    pdf.drawString(50, 100, "Thank you for renting with us!")

    # Save PDF
    pdf.save()
    buffer.seek(0)

    # Create Flask Response
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={title.replace(' ', '_').lower()}_{customer_id}.pdf"
    return response
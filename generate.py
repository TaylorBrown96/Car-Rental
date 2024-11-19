from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import sqlite3
from io import BytesIO


def vehicleReport():
    conn = sqlite3.connect("car_rental.db")
    # Fetch data from the database
    cursor = conn.cursor()

    # Current date for comparison
    current_date = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    # Query for cars rented
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
    """, (current_date, current_date))
    rented_cars = cursor.fetchall()

    # Query for cars in-house
    cursor.execute("""
        SELECT VehicleID, v.Year || ' ' || v.Make || ' ' || v.Model AS Name 
        FROM Vehicles  v
        WHERE Available = 'Yes'
    """)
    in_house_cars = cursor.fetchall()

    # Query for revenue
    cursor.execute("""
        SELECT SUM(r.TotalPrice) AS Revenue
        FROM Reservations r
    """)
    revenue = cursor.fetchone()[0] or 0.0

    # Query for unavailable cars without reservations
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
    """, (current_date, current_date))
    unavailable_cars = cursor.fetchall()

    conn.close()

    # Use BytesIO as an in-memory buffer for the PDF
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    
    # Report Title
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 750, "Car Rental Report")
    pdf.drawString(50, 735, f"Date: {current_date.replace('_', ' at ')}")

    # Rented Cars Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "Cars Currently Rented:")
    pdf.setFont("Helvetica", 12)
    y = 685
    for car in rented_cars:
        pdf.drawString(50, y, f"Vehicle ID: {car[0]}, Name: {car[1]}, Rented From: {car[2]} - {car[3]}")
        y -= 15

    # In-House Cars Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y - 15, "Cars In-House/Available For Rent:")
    pdf.setFont("Helvetica", 12)
    y -= 30
    for car in in_house_cars:
        pdf.drawString(50, y, f"Vehicle ID: {car[0]}, Name: {car[1]}")
        y -= 15

    # Revenue Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y - 15, "Total Revenue Earned:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(200, y - 15, f"${revenue:.2f}")
    y -= 30

    # Unavailable Cars Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y - 15, "Unavailable Cars Without Current Reservations:")
    pdf.setFont("Helvetica", 12)
    y -= 30
    for car in unavailable_cars:
        pdf.drawString(50, y, f"Vehicle ID: {car[0]}, Name: {car[1]}")
        y -= 15

    pdf.save()
    pdf_buffer.seek(0)  # Move to the start of the BytesIO buffer

    # Prepare the response
    response = make_response(pdf_buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={current_date}_report.pdf"

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
    cursor.execute("SELECT Address, Phone FROM Locations WHERE LocationID = ?", (reservation[7],))
    pickup_details = cursor.fetchone()
    pickup_address, pickup_phone = pickup_details[0], pickup_details[1]

    cursor.execute("SELECT Address, Phone FROM Locations WHERE LocationID = ?", (reservation[8],))
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
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import sqlite3
from io import BytesIO


def generate():
    # Fetch data from the database
    conn = sqlite3.connect("car_rental.db")  # Replace with your database name
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
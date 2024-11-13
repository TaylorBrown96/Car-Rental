import sqlite3

# Example database path
db_path = 'car_rental.db'


def reset_database():
    # List of tables to clear, excluding the Users table
    tables_to_clear = ["Invoice", "Locations", "RentalPlans", "Reservations", "ServiceIntervals", "Vehicles"]

    # Connect to the database and clear each table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table in tables_to_clear:
        cursor.execute(f"DELETE FROM {table}")

    conn.commit()
    conn.close()
    
    print("Database reset complete\n")


def insert_locations_data():
    # Example location data
    location_data = [
        ("123 Maple St, Fayetteville, NC 28301", "910-555-0123"),
        ("456 Oak Ave, Fayetteville, NC 28303", "910-555-0456"),
        ("789 Pine Dr, Fayetteville, NC 28305", "910-555-0789")
    ]

    # Insert data into the Locations table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for address, phone in location_data:
        cursor.execute(
            "INSERT INTO Locations (LocationID, Address, Phone) VALUES (NULL, ?, ?)", 
            (address, phone)
        )

    conn.commit()
    conn.close()
    
    print("Location data inserted")
    

def insert_vehicle_data():
    # Real-world vehicle data
    vehicle_data = [
        ("Toyota", "Camry", 2018, "Sedan", 35000, "Automatic", 4, "Operational", "Yes", "https://th.bing.com/th/id/R.ee3a8eb625b80e8a339ba413b6083356?rik=EqglPbjWgbUQWA&pid=ImgRaw&r=0", 1),
        ("Ford", "F-150", 2020, "Truck", 25000, "Automatic", 4, "Operational", "Yes", "https://th.bing.com/th/id/OIP.qR61L25gB85KDDnqe0zYAQHaEo?rs=1&pid=ImgDetMain", 2),
        ("Chevrolet", "Tahoe", 2019, "SUV", 45000, "Automatic", 4, "In Repair", "No", "https://a4e5e0ff95b1cab202bf-6a8356f83a523ee2fe1677c35304c3f3.ssl.cf1.rackcdn.com/1GNSKCKC1KR265544/9e9f86b1524f6461a3ef78ce6de82f54.jpg", 3),
        ("Honda", "Accord", 2017, "Sedan", 50000, "Automatic", 4, "Operational", "Yes", "https://pictures.dealer.com/s/showcasehonda/0181/bf13f6d512d4f5ace1c36ea19ae4e7e6x.jpg", 1),
        ("Nissan", "Altima", 2016, "Sedan", 65000, "Automatic", 4, "In Repair", "No", "https://static0.topspeedimages.com/wordpress/wp-content/uploads/crop/201610/nissan-altima-driven-7_1600x0w.jpg", 2),
        ("Jeep", "Wrangler", 2015, "SUV", 75000, "Manual", 2, "Operational", "Yes", "https://hips.hearstapps.com/amv-prod-cad-assets.s3.amazonaws.com/wp-content/uploads/2015/02/2015-Jeep-Wrangler-Willys-202.jpg", 3),
        ("BMW", "3 Series", 2021, "Sedan", 15000, "Automatic", 4, "Operational", "Yes", "https://images.hgmsites.net/hug/2020-bmw-3-series-m340i-xdrive_100745229_h.jpg", 1),
        ("Audi", "Q5", 2018, "SUV", 30000, "Automatic", 4, "In Repair", "No", "https://cdn.motor1.com/images/mgl/rlgVY/s1/2018-audi-q5-first-drive.jpg", 2),
        ("Tesla", "Model S", 2020, "Sedan", 20000, "Automatic", 4, "Operational", "Yes", "https://media.ed.edmunds-media.com/tesla/model-s/2019/oem/2019_tesla_model-s_sedan_performance_fq_oem_1_815.jpg", 3),
        ("Ford", "Mustang", 2019, "Coupe", 22000, "Manual", 2, "Operational", "Yes", "https://media.carsandbids.com/cdn-cgi/image/width=1800,quality=70/ee7f173e46ec801a48d1673c50f9cebaa1bf2854/photos/307QRazV-A_eASqsRsp-(edit).jpg?t=167518885655", 1),
        ("Chevrolet", "Malibu", 2016, "Sedan", 80000, "Automatic", 4, "In Repair", "No", "https://blog.consumerguide.com/wp-content/uploads/sites/2/2016/12/Screen-Shot-2016-12-21-at-2.47.29-PM-1024x640.png", 2),
        ("Toyota", "RAV4", 2017, "SUV", 60000, "Automatic", 4, "Operational", "Yes", "https://media.ed.edmunds-media.com/toyota/rav4/2017/oem/2017_toyota_rav4_4dr-suv_se_fq_oem_1_600.jpg", 3),
        ("Honda", "Civic", 2015, "Sedan", 90000, "Automatic", 4, "Operational", "Yes", "https://i.pinimg.com/736x/55/96/e6/5596e69dab32f19d87a3b025cdd8ada0.jpg", 1),
        ("Nissan", "Sentra", 2018, "Sedan", 40000, "Automatic", 4, "Operational", "Yes", "https://vehicle-images.dealerinspire.com/75a0-110009814/3N1AB7AP0JY280015/99f1ae0d6551325e58d14476c524044a.jpg", 2),
        ("Jeep", "Grand Cherokee", 2019, "SUV", 35000, "Automatic", 4, "In Repair", "No", "https://cdn.motor1.com/images/mgl/W02Jr/s1/2019-jeep-grand-cherokee-limited-x-review.webp", 3),
        ("BMW", "X5", 2021, "SUV", 18000, "Automatic", 4, "Operational", "Yes", "https://www.automotiveaddicts.com/wp-content/uploads/2021/07/2021-bmw-x5-xdrive45e.jpg", 1),
        ("Audi", "A4", 2017, "Sedan", 55000, "Automatic", 4, "Operational", "Yes", "https://www.motortrend.com/uploads/sites/5/2017/07/2017-Audi-A4-20T-Quattro-front-three-quarter-e1500572290866.jpg", 2),
        ("Tesla", "Model 3", 2022, "Sedan", 10000, "Automatic", 4, "Operational", "Yes", "https://www.mclarencf.com/imagetag/258/4/l/Used-2022-Tesla-Model-3.jpg", 3),
        ("Ford", "Explorer", 2019, "SUV", 30000, "Automatic", 4, "In Repair", "No", "https://static.overfuel.com/photos/178/117877/image-1.webp", 1),
        ("Chevrolet", "Equinox", 2020, "SUV", 20000, "Automatic", 4, "Operational", "Yes", "https://images.cars.com/cldstatic/wp-content/uploads/chevrolet-equinox-2019-exterior-front-three-quarter-oem.jpg", 2),
        ("Toyota", "Highlander", 2018, "SUV", 40000, "Automatic", 4, "Operational", "Yes", "https://www.edmunds.com/assets/m/for-sale/3f-5tdjzrfh4js546570/img-1-600x400.jpg", 3),
        ("Honda", "Pilot", 2021, "SUV", 15000, "Automatic", 4, "Operational", "Yes", "https://www.motortrend.com/uploads/sites/5/2020/06/2021-Honda-Pilot-Elite-2.jpg?w=768&width=768&q=75&format=webp", 1),
        ("Nissan", "Rogue", 2017, "SUV", 70000, "Automatic", 4, "In Repair", "No", "https://media.ed.edmunds-media.com/nissan/rogue/2017/oem/2017_nissan_rogue_4dr-suv_sv_fq_oem_1_1600.jpg", 2),
        ("Jeep", "Compass", 2019, "SUV", 30000, "Automatic", 4, "Operational", "Yes", "https://drivingtorque.com/wp-content/uploads/2019/03/2019-jeep-compass-grey-front-side-review-roadtest.jpg", 3),
        ("BMW", "5 Series", 2018, "Sedan", 40000, "Automatic", 4, "Operational", "Yes", "https://media.ed.edmunds-media.com/for-sale/8b-wbaja7c5xjwc75942/img-1-600x400.jpg", 1),
        ("Audi", "Q7", 2020, "SUV", 25000, "Automatic", 4, "In Repair", "No", "https://images.ctfassets.net/c9t6u0qhbv9e/2020AudiQ7TestDriveReviewsummary/9f9d5d4a0d9e7c0618a8d74039b4a2b8/2020_Audi_Q7_Test_Drive_Review_summaryImage.jpeg", 2),
        ("Tesla", "Model X", 2019, "SUV", 20000, "Automatic", 4, "Operational", "Yes", "https://vehicle-images.dealerinspire.com/5466-110008891/5YJXCDE29KF180249/c717eb0a96b5afd22cd3822da7ca126d.jpg", 3),
        ("Ford", "Edge", 2018, "SUV", 50000, "Automatic", 4, "Operational", "Yes", "https://cloudflareimages.dealereprocess.com/resrc/images/c_limit,fl_lossy,w_500/v1/dvp/2297/10446110083/Pre-Owned-2018-Ford-Edge-Titanium-ID10446110083-aHR0cDovL2ltYWdlcy51bml0c2ludmVudG9yeS5jb20vdXBsb2Fkcy9waG90b3MvMC8yMDI0LTEwLTMxLzItMTkxODU5MjgtNjcyNDBiMmZjNzhhMS5qcGc=", 1),
        ("Chevrolet", "Traverse", 2017, "SUV", 60000, "Automatic", 4, "Operational", "Yes", "https://media.ed.edmunds-media.com/chevrolet/traverse/2017/ot/2017_chevrolet_traverse_LIFE1_ot_207173_600.jpg", 2),
        ("Toyota", "Corolla", 2015, "Sedan", 90000, "Automatic", 4, "Operational", "Yes", "https://images.ctfassets.net/c9t6u0qhbv9e/2015ToyotaCorollaTestDriveReviewsummary/dbf5731cc3b411907236abfb4024c13f/2015_Toyota_Corolla_Test_Drive_Review_summaryImage.jpeg", 3),
        ("Tesla", "Cybertruck", 2023, "Truck", 20000, "Automatic", 4, "Operational", "Yes", "https://www.teslarati.com/wp-content/uploads/2023/07/tesla-cybertruck-texas-elon-musk-scaled-e1688899667930.jpeg", 3)
    ]

    def determine_service_id(mileage):
        if mileage <= 5000:
            return 1
        elif mileage <= 10000:
            return 2
        elif mileage <= 15000:
            return 3
        elif mileage <= 25000:
            return 4
        elif mileage <= 50000:
            return 5
        else:
            return 9

    # Insert data into the Vehicles table with ServiceID
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for make, model, year, type_, mileage, transmission, num_doors, repair_status, available, photos, location_id in vehicle_data:
        service_id = determine_service_id(mileage)
        cursor.execute(
            "INSERT INTO Vehicles (VehicleID, Make, Model, Year, Type, Mileage, Transmission, NumDoors, RepairStatus, Available, Photos, LocationID, ServiceID) "
            "VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (make, model, year, type_, mileage, transmission, num_doors, repair_status, available, photos, location_id, service_id)
        )

    conn.commit()
    conn.close()
    
    print("Vehicle data inserted")


def insert_service_intervals_data():
    # Define the service intervals data
    service_intervals_data = [
        (1, "Basic Maintenance", "Oil change and filter replacement", 5000),
        (2, "Routine Check", "Tire rotation and brake inspection", 10000),
        (3, "Intermediate Service", "Replace air filter and inspect belts", 15000),
        (4, "Major Service", "Full inspection and fluid replacements", 25000),
        (5, "Comprehensive Service", "Inspect suspension and alignment", 50000),
        (9, "No Service Required", "Car to be sold", 1000000)
    ]

    # Insert data into the ServiceIntervals table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for service_id, type_, description, mileage_checkpoint in service_intervals_data:
        cursor.execute(
            "INSERT INTO ServiceIntervals (ServiceID, Type, Description, MileageCheckpoint) "
            "VALUES (?, ?, ?, ?)",
            (service_id, type_, description, mileage_checkpoint)
        )

    conn.commit()
    conn.close()
    
    print("Service intervals data inserted")


def main():
    reset_database()
    insert_locations_data()
    insert_vehicle_data()
    insert_service_intervals_data()


if __name__ == "__main__":
    main()

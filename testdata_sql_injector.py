import sqlite3

# Example database path
db_path = 'car_rental.db'


def reset_database():
    # List of tables to clear, excluding the Users table
    tables_to_clear = ["Invoice", "RentalPlans", "Reservations", "ServiceIntervals", "Vehicles"]

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
        ("123 Maple St, Fayetteville, NC 28301", "910-555-0123", "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d5408.484911079588!2d-78.90126389999999!3d35.0049638!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89ab13a3ed566e8f%3A0xaa35bb314262d448!2s123%20Maple%20St%2C%20Fayetteville%2C%20NC%2028306!5e1!3m2!1sen!2sus!4v1731541443139!5m2!1sen!2sus"),
        ("456 Oak Ave, Fayetteville, NC 28303", "910-555-0456", "https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d21615.609884123245!2d-78.8924896!3d35.0742206!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89ab6cdce1db451f%3A0x8b543dcd41a3a823!2sFayetteville%20State%20University!5e1!3m2!1sen!2sus!4v1726339737300!5m2!1sen!2sus"),
        ("789 Pine Dr, Fayetteville, NC 28305", "910-555-0789", "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d5405.718408863817!2d-78.89200022291364!3d35.04678966456243!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89ab132926387d3d%3A0x6ce1bc187c70cdba!2s789%20Pine%20St%2C%20Fayetteville%2C%20NC%2028301!5e1!3m2!1sen!2sus!4v1731541572359!5m2!1sen!2sus")
    ]

    # Insert data into the Locations table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for address, phone, gmaps in location_data:
        cursor.execute(
            "INSERT INTO Locations (LocationID, Address, Phone, gmaps) VALUES (NULL, ?, ?, ?)", 
            (address, phone, gmaps)
        )

    conn.commit()
    conn.close()
    
    print("Location data inserted")
    

def insert_vehicle_data():
    # Real-world vehicle data
    vehicle_data = [
    ("Toyota", "Camry", 2018, "Sedan", 35000, "Automatic", 4, "Operational", "Yes", "https://th.bing.com/th/id/R.ee3a8eb625b80e8a339ba413b6083356?rik=EqglPbjWgbUQWA&pid=ImgRaw&r=0ㄹhttps://cdn.motor1.com/images/mgl/mv7vR/s1/2018-toyota-camry-xse-review.jpgㄹhttps://img.sm360.ca/images/article/laking-motors-inc/58080/2019-toyota-camry-50721553879732375.jpg", 10, "Fuel-efficient, Reliable, Spacious interior, Advanced safety, Smooth ride", 
     "The 2018 Toyota Camry is a fuel-efficient mid-sized sedan perfect for daily commuting and family trips. It offers a smooth, comfortable ride with modern features and reliable safety scores.", "FWD"),
    
    ("Ford", "F-150", 2020, "Truck", 25000, "Automatic", 4, "Operational", "Yes", "https://th.bing.com/th/id/OIP.qR61L25gB85KDDnqe0zYAQHaEo?rs=1&pid=ImgDetMainㄹhttps://www.autotrader.ca/editorial/media/184255/2020-ford-f-150-king-ranch-4x4-02-jm.jpg?width=1920&height=1080&v=1d66618bd1f4640ㄹhttps://img2.carmax.com/assets/26328010/hero.jpg?width=400&height=300", 11, "Strong towing capacity, Spacious interior, Durable, High payload, Comfortable seats", 
     "The 2020 Ford F-150 is a robust full-size truck known for its high towing and payload capacities. Ideal for both work and recreational use, it combines power with modern comfort and safety.", "4WD"),

    ("Chevrolet", "Tahoe", 2019, "SUV", 45000, "Automatic", 4, "In Repair", "No", "https://a4e5e0ff95b1cab202bf-6a8356f83a523ee2fe1677c35304c3f3.ssl.cf1.rackcdn.com/1GNSKCKC1KR265544/9e9f86b1524f6461a3ef78ce6de82f54.jpgㄹhttps://hips.hearstapps.com/hmg-prod/amv-prod-cad-assets/wp-content/uploads/2018/03/2018-Chevrolet-Tahoe-RST-Edition-107.jpg?fill=2:1&resize=1200:*ㄹhttps://www.legendcarcompany.com/galleria_images/435/435_main_l.jpg", 12, "Spacious, Powerful engine, Family-friendly, High towing capacity, All-terrain capability", 
     "The 2019 Chevrolet Tahoe is a large SUV with ample seating for families and excellent towing capability. It’s perfect for those who need both space and power in one package.", "4WD"),

    ("Honda", "Accord", 2017, "Sedan", 50000, "Automatic", 4, "Operational", "Yes", "https://pictures.dealer.com/s/showcasehonda/0181/bf13f6d512d4f5ace1c36ea19ae4e7e6x.jpgㄹhttps://media.drive.com.au/obj/tx_q:50,rs:auto:1920:1080:1/caradvice/private/48389d4a586f92c5f970c6709e37b927ㄹhttps://hips.hearstapps.com/hmg-prod/amv-prod-cad-assets/wp-content/uploads/2017/08/2017-honda-accord-in-depth-model-review-car-and-driver-photo-672229-s-original.jpg?crop=1.00xw:0.819xh;0,0.181xh&resize=1200:*", 10, "Reliable, High resale value, Comfortable, Advanced safety, Smooth handling", 
     "The 2017 Honda Accord is a stylish and reliable sedan that offers a comfortable interior and advanced safety features. Known for its longevity, it’s an ideal choice for families and commuters alike.", "FWD"),

    ("Nissan", "Altima", 2016, "Sedan", 65000, "Automatic", 4, "In Repair", "No", "https://static0.topspeedimages.com/wordpress/wp-content/uploads/crop/201610/nissan-altima-driven-7_1600x0w.jpgㄹhttps://www.autoblog.com/.image/t_share/MjA5MTUzOTY3NzY4MjE3MjAw/image-placeholder-title.jpgㄹhttps://www.motortrend.com/uploads/sites/11/2015/09/2016-nissan-altima-sr-front-three-quarter-inside-03.jpg", 11, "Comfortable, Efficient, Quiet ride, Affordable maintenance, Fuel-efficient", 
     "The 2016 Nissan Altima provides a quiet, comfortable ride and good fuel economy, making it a reliable choice for long drives and city commutes.", "FWD"),

    ("Jeep", "Wrangler", 2015, "SUV", 75000, "Manual", 2, "Operational", "Yes", "https://hips.hearstapps.com/amv-prod-cad-assets.s3.amazonaws.com/wp-content/uploads/2015/02/2015-Jeep-Wrangler-Willys-202.jpgㄹhttps://cdn.dealeraccelerate.com/adrenalin/1/610/15332/1920x1440/2015-jeep-wrangler-unlimited-saharaㄹhttps://www.vehiclehistory.com/uploads/2015-Jeep-Wrangler.jpg", 12, "Off-road capability, Iconic design, Rugged, Durable, Convertible option", 
     "The 2015 Jeep Wrangler is a rugged, off-road vehicle designed for adventure. With its legendary 4x4 capabilities, it’s perfect for outdoor enthusiasts and thrill-seekers.", "4WD"),

    ("BMW", "3 Series", 2021, "Sedan", 15000, "Automatic", 4, "Operational", "Yes", "https://images.hgmsites.net/hug/2020-bmw-3-series-m340i-xdrive_100745229_h.jpgㄹhttps://www.carparisonleasing.co.uk/media/cache/blog_detail_image_1170/cc-uploads/bbbeb225/BMW%20330e%20parked%20by%20bush.jpgㄹhttps://images.hgmsites.net/hug/2021-bmw-3-series_100772742_h.jpg", 10, "Luxury interior, High performance, Advanced technology, Smooth handling, Stylish design", 
     "The 2021 BMW 3 Series combines luxury and performance in a compact sedan. It’s equipped with a high-tech interior and powerful engine options for a premium driving experience.", "RWD"),

    ("Audi", "Q5", 2018, "SUV", 30000, "Automatic", 4, "In Repair", "No", "https://cdn.motor1.com/images/mgl/rlgVY/s1/2018-audi-q5-first-drive.jpgㄹhttps://cdn.motor1.com/images/mgl/0kVNz/s1/2018-audi-sq5-review.webpㄹhttps://static.overfuel.com/photos/19/8675/image-2-thumb.webp", 11, "Premium interior, Smooth handling, Quiet ride, All-wheel drive, Tech-savvy", 
     "The 2018 Audi Q5 is a luxury compact SUV with a refined interior and balanced performance. It offers a quiet, comfortable ride with excellent handling.", "AWD"),

    ("Tesla", "Model S", 2020, "Sedan", 20000, "Automatic", 4, "Operational", "Yes", "https://media.ed.edmunds-media.com/tesla/model-s/2019/oem/2019_tesla_model-s_sedan_performance_fq_oem_1_815.jpgㄹhttps://car-images.bauersecure.com/wp-images/12947/tesla-model-s-07.jpgㄹhttps://cdn.inventoryrsc.com/362740581_66de2780040226147c2b9cea.jpg", 12, "Electric, Advanced tech features, Long range, Fast acceleration, Futuristic design", 
     "The 2020 Tesla Model S is a high-performance electric sedan with impressive range and cutting-edge technology. It’s perfect for eco-conscious drivers who want luxury and innovation.", "AWD"),

    ("Ford", "Mustang", 2019, "Coupe", 22000, "Manual", 2, "Operational", "Yes", "https://media.carsandbids.com/cdn-cgi/image/width=1800,quality=70/ee7f173e46ec801a48d1673c50f9cebaa1bf2854/photos/307QRazV-A_eASqsRsp-(edit).jpg?t=167518885655ㄹhttps://i.ytimg.com/vi/MV21zsGLS9k/maxresdefault.jpgㄹhttps://media.carsandbids.com/cdn-cgi/image/width=1800,quality=70/171ab1e538119e13fa98382f268326fc825fdc20/photos/rE6elw5b.kMFUF-xOh-(edit).jpg?t=162958389783", 10, "Sporty design, Powerful engine, Iconic styling, High performance, Customizable options", 
     "The 2019 Ford Mustang is an iconic sports car that combines aggressive styling with powerful engine options, providing a thrilling driving experience.", "RWD"),

    ("Chevrolet", "Equinox", 2020, "SUV", 20000, "Automatic", 4, "Operational", "Yes", "https://images.cars.com/cldstatic/wp-content/uploads/chevrolet-equinox-2019-exterior-front-three-quarter-oem.jpgㄹhttps://vehicle-images.dealerinspire.com/6832-110007843/thumbnails/large/3GNAXJEV7LL248769/44f9c3474de9526299eb62936bc4267f.jpgㄹhttps://vehicle-images.dealerinspire.com/9428-110008730/3GNAXKEV6LS734551/1645ead1a03d80970af2ccfd5e3c1f43.jpg", 11, "Compact, Fuel-efficient, Smooth ride, Advanced safety, Affordable", 
     "The 2020 Chevrolet Equinox is a compact SUV offering a smooth ride and excellent fuel efficiency, perfect for small families and urban driving.", "FWD"),

    ("Toyota", "RAV4", 2017, "SUV", 60000, "Automatic", 4, "Operational", "Yes", "https://media.ed.edmunds-media.com/toyota/rav4/2017/oem/2017_toyota_rav4_4dr-suv_se_fq_oem_1_600.jpgㄹhttps://www.autotrader.ca/editorial/media/61597/2017-toyota-rav4-limited-01-ts.jpg?width=1920&height=1080&v=1d249378c6dca00ㄹhttps://media.ed.edmunds-media.com/toyota/rav4-hybrid/2017/oem/2017_toyota_rav4-hybrid_4dr-suv_limited_fq_oem_1_1600.jpg", 12, "Reliable, Good resale value, Spacious interior, Off-road capable, Family-friendly", 
     "The 2017 Toyota RAV4 is a reliable compact SUV with a reputation for longevity and high resale value. It’s a practical choice for families and outdoor adventures.", "AWD"),

    ("Honda", "Civic", 2015, "Sedan", 90000, "Automatic", 4, "Operational", "Yes", "https://i.pinimg.com/736x/55/96/e6/5596e69dab32f19d87a3b025cdd8ada0.jpgㄹhttps://www.cnet.com/a/img/resize/a5907b50d1dfe2a174db8f50d394091afae6e6c6/hub/2015/07/22/d0cdb061-f1ba-4be6-b283-a409508aa2e3/hondacivicsi-49.jpg?auto=webp&width=768ㄹhttps://img2.carmax.com/assets/26230351/hero.jpg?width=400&height=300", 10, "Fuel-efficient, Compact, Easy to park, Low maintenance, Reliable", 
     "The 2015 Honda Civic is a compact and fuel-efficient sedan that’s easy to maneuver in the city while also offering a reliable performance on highways.", "FWD"),

    ("Nissan", "Sentra", 2018, "Sedan", 40000, "Automatic", 4, "Operational", "Yes", "https://vehicle-images.dealerinspire.com/75a0-110009814/3N1AB7AP0JY280015/99f1ae0d6551325e58d14476c524044a.jpgㄹhttps://www.motortrend.com/uploads/2022/03/2022-Nissan-Sentra-SR-19.jpgㄹhttps://vehicle-images.dealerinspire.com/44bb-110007493/3N1AB7AP7JY237470/427cea0a88585e3f1a273ccffd79bff3.jpg", 11, "Affordable, Reliable, Low maintenance, Compact, Comfortable ride", 
     "The 2018 Nissan Sentra is an affordable compact sedan with a focus on reliability and low maintenance costs, ideal for budget-conscious drivers.", "FWD"),

    ("Jeep", "Grand Cherokee", 2019, "SUV", 35000, "Automatic", 4, "In Repair", "No", "https://cdn.motor1.com/images/mgl/W02Jr/s1/2019-jeep-grand-cherokee-limited-x-review.webpㄹhttps://images.dealersync.com/cloud/userdocumentprod/2563/Photos/473709/20200109001526976_S9I0IOBO1FYOID.jpg?_=a1303ee67066b5c767166f6a4bf4cf5b477cd314ㄹhttps://www.jonathanmotorcars.com/imagetag/1254/2/l/Used-2019-Jeep-Grand-Cherokee-Altitude-1614821161.jpg", 12, "Off-road capable, Luxurious interior, Powerful engine, Spacious, Family-friendly", 
     "The 2019 Jeep Grand Cherokee offers luxury and off-road capability, perfect for those who need a versatile SUV for both city and rugged terrains.", "4WD"),

    ("BMW", "X5", 2021, "SUV", 18000, "Automatic", 4, "Operational", "Yes", "https://www.automotiveaddicts.com/wp-content/uploads/2021/07/2021-bmw-x5-xdrive45e.jpgㄹhttps://images.ctfassets.net/c9t6u0qhbv9e/2021BMWX5TestDriveReviewsummary/06de782ff0a97be63ab51e79fc4195ed/2021_BMW_X5_Test_Drive_Review_summaryImage.jpegㄹhttps://www.autotrader.ca/editorial/media/187091/2021-bmw-x5-xdrive45e-03-jm.jpg?width=1920&height=1080&v=1d69c84f8841470", 10, "Luxurious, Powerful engine, High-tech, Comfortable, Versatile", 
     "The 2021 BMW X5 is a luxury SUV with a powerful engine and a sophisticated interior, offering a high-end driving experience for those who value comfort and performance.", "AWD"),

    ("Audi", "A4", 2017, "Sedan", 55000, "Automatic", 4, "Operational", "Yes", "https://www.motortrend.com/uploads/sites/5/2017/07/2017-Audi-A4-20T-Quattro-front-three-quarter-e1500572290866.jpgㄹhttps://www.carsoup.com/blog/content/images/2017/12/2017_Audi_A4_20_TFSI_Quattro_Front_View-3.jpgㄹhttps://media.carsandbids.com/cdn-cgi/image/width=2080,quality=70/438ad923cef6d8239e95d61e7d6849486bae11d9/photos/KVWlGZEY-YAc4hg16kL-(edit).jpg?t=167803227472", 11, "Premium features, Smooth handling, Stylish design, Advanced technology, Reliable", 
     "The 2017 Audi A4 is a compact luxury sedan with a premium interior and smooth handling, ideal for those who value quality and style.", "AWD"),

    ("Tesla", "Model 3", 2022, "Sedan", 10000, "Automatic", 4, "Operational", "Yes", "https://www.mclarencf.com/imagetag/258/4/l/Used-2022-Tesla-Model-3.jpgㄹhttps://getusedtesla.com/wp-content/uploads/2022/11/Photo-Oct-31-2022-5-27-29-PM-1024x768.jpgㄹhttps://www.mclarencf.com/imagetag/258/main/l/Used-2022-Tesla-Model-3.jpg", 12, "Electric, Tech advanced, Long range, Futuristic design, Eco-friendly", 
     "The 2022 Tesla Model 3 is an electric sedan with advanced technology and impressive range, ideal for tech-savvy and eco-conscious drivers.", "RWD"),

    ("Ford", "Explorer", 2019, "SUV", 30000, "Automatic", 4, "In Repair", "No", "https://static.overfuel.com/photos/178/117877/image-1.webpㄹhttps://hips.hearstapps.com/hmg-prod/images/2019-ford-explorer-limited-luxury-edition-3-1560360672.jpg?crop=1.00xw:0.846xh;0,0.127xh&resize=2048:*ㄹhttps://www.hardyforddallas.com/static/dealer-14780/1098609.png", 10, "Spacious, Versatile, Comfortable, Family-friendly, All-terrain capable", 
     "The 2019 Ford Explorer is a spacious SUV designed for families, with versatile seating and cargo options, making it ideal for road trips and everyday use.", "4WD"),

    ("Chevrolet", "Malibu", 2016, "Sedan", 80000, "Automatic", 4, "In Repair", "No", "https://blog.consumerguide.com/wp-content/uploads/sites/2/2016/12/Screen-Shot-2016-12-21-at-2.47.29-PM-1024x640.pngㄹhttps://blog.consumerguide.com/wp-content/uploads/sites/2/2016/12/Screen-Shot-2016-12-21-at-2.47.29-PM-1024x640.pngㄹhttps://www.autotrader.ca/editorial/media/138219/2018-chevrolet-malibu-hybrid-01-bh.jpg?width=1920&height=1080&v=1d399bd02452170", 11, "Comfortable, Good fuel economy, Reliable, Spacious, Advanced safety", 
     "The 2016 Chevrolet Malibu is a mid-size sedan known for its comfortable ride and good fuel economy, ideal for daily commutes.", "FWD"),
    
    ("Chevrolet", "Traverse", 2017, "SUV", 60000, "Automatic", 4, "Operational", "Yes", "https://media.ed.edmunds-media.com/chevrolet/traverse/2017/ot/2017_chevrolet_traverse_LIFE1_ot_207173_600.jpgㄹhttps://content.homenetiol.com/2000292/2177761/0x0/e933d974e22b4f43a67a4042dca63ded.jpgㄹhttps://img2.carmax.com/assets/26410474/hero.jpg?width=400&height=300", 11, "Spacious, Family-friendly, Cargo space, Reliable, Comfortable", 
     "The 2017 Chevrolet Traverse is a mid-size SUV offering ample seating and cargo space, making it an excellent choice for families and long road trips.", "FWD"),

    ("Toyota", "Corolla", 2015, "Sedan", 90000, "Automatic", 4, "Operational", "Yes", "https://images.ctfassets.net/c9t6u0qhbv9e/2015ToyotaCorollaTestDriveReviewsummary/dbf5731cc3b411907236abfb4024c13f/2015_Toyota_Corolla_Test_Drive_Review_summaryImage.jpegㄹhttps://imageio.forbes.com/blogs-images/danroth/files/2017/12/2018-toyota-corolla-se_01-1200x798.jpg?format=jpg&height=900&width=1600&fit=boundsㄹhttps://upload.wikimedia.org/wikipedia/commons/f/f1/Toyota_Corolla_1.8_GL_2015_%2817416299585%29.jpg", 12, "Reliable, Fuel-efficient, Compact, Low maintenance, Safe", 
     "The 2015 Toyota Corolla is a compact sedan known for its reliability and excellent fuel economy, making it a practical and cost-effective option.", "FWD"),

    ("Tesla", "Cybertruck", 2023, "Truck", 20000, "Automatic", 4, "Operational", "Yes", "https://www.teslarati.com/wp-content/uploads/2023/07/tesla-cybertruck-texas-elon-musk-scaled-e1688899667930.jpegㄹhttps://www.greendrive-accessories.com/blog/wp-content/uploads/2024/01/Tesla-Cybertruck-Towing-Prowess-and-Range-Revelations.pngㄹhttps://www.kbb.com/wp-content/uploads/2024/06/2024-tesla-cybertruck-front-left-3qtr-3.jpg", 12, "Electric, Futuristic design, High durability, All-terrain, Innovative", 
     "The 2023 Tesla Cybertruck is an all-electric pickup truck with a futuristic design, offering high durability and impressive off-road capabilities.", "AWD"),

    ("Ford", "Edge", 2018, "SUV", 50000, "Automatic", 4, "Operational", "Yes", "https://cloudflareimages.dealereprocess.com/resrc/images/c_limit,fl_lossy,w_500/v1/dvp/2297/10446110083/Pre-Owned-2018-Ford-Edge-Titanium-ID10446110083-aHR0cDovL2ltYWdlcy51bml0c2ludmVudG9yeS5jb20vdXBsb2Fkcy9waG90b3MvMC8yMDI0LTEwLTMxLzItMTkxODU5MjgtNjcyNDBiMmZjNzhhMS5qcGc=ㄹhttps://media.ed.edmunds-media.com/ford/edge/2017/oem/2017_ford_edge_4dr-suv_titanium_rq_oem_2_815.jpgㄹhttps://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSWgf_vazhlsMhroVFg4W1JM_81trFdglM3AbS-0yI67NzzatLMo4jWQBVU-acfgWyrm4o&usqp=CAU", 10, "Comfortable, Tech features, Smooth handling, Reliable, Spacious", 
     "The 2018 Ford Edge is a well-rounded SUV with a comfortable interior and advanced tech features, providing a smooth driving experience for families.", "AWD"),

    ("Honda", "Pilot", 2021, "SUV", 15000, "Automatic", 4, "Operational", "Yes", "https://www.motortrend.com/uploads/sites/5/2020/06/2021-Honda-Pilot-Elite-2.jpg?w=768&width=768&q=75&format=webpㄹhttps://images.ctfassets.net/c9t6u0qhbv9e/2021HondaPilotTestDriveReviewsummary/5027f10755fec9d35226ab4cd93eecab/2021_Honda_Pilot_Test_Drive_Review_summaryImage.jpegㄹhttps://images.hgmsites.net/hug/2021-honda-pilot_100749543_h.jpg", 10, "Spacious, Reliable, Comfortable, Family-oriented, Versatile", 
     "The 2021 Honda Pilot is a spacious mid-size SUV known for its reliability and comfort, ideal for families looking for a versatile vehicle.", "AWD"),

    ("Nissan", "Rogue", 2017, "SUV", 70000, "Automatic", 4, "In Repair", "No", "https://media.ed.edmunds-media.com/nissan/rogue/2017/oem/2017_nissan_rogue_4dr-suv_sv_fq_oem_1_1600.jpgㄹhttps://cdn-ds.com/blogs-media/sites/603/2017/03/07070950/2017-Nissan-Rogue_o.jpgㄹhttps://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-TDV_lHRRDzHFIz65l4PzttHR0PxpOoE60A&s", 11, "Compact, Fuel-efficient, Reliable, Affordable, Practical", 
     "The 2017 Nissan Rogue is a compact SUV with excellent fuel efficiency and versatile cargo space, making it a practical choice for urban dwellers.", "AWD"),

    ("Jeep", "Compass", 2019, "SUV", 30000, "Automatic", 4, "Operational", "Yes", "https://drivingtorque.com/wp-content/uploads/2019/03/2019-jeep-compass-grey-front-side-review-roadtest.jpgㄹhttps://platform.cstatic-images.com/xlarge/in/v2/stock_photos/7b125e6c-c825-4c2d-b63d-2af09e984fdb/994abba6-5148-4216-92f9-edcbc07070b8.pngㄹhttps://drivingtorque.com/wp-content/uploads/2019/03/2019-jeep-compass-grey-front-side-review-roadtest.jpg", 12, "Off-road capable, Compact, Stylish, Reliable, Adventure-ready", 
     "The 2019 Jeep Compass is a compact SUV with off-road capabilities, offering a balance of style and adventure for city and trail use.", "4WD"),

    ("BMW", "5 Series", 2018, "Sedan", 40000, "Automatic", 4, "Operational", "Yes", "https://media.ed.edmunds-media.com/for-sale/8b-wbaja7c5xjwc75942/img-1-600x400.jpgㄹhttps://autodesignmagazine.com/wp-content/uploads/2017/02/2017022102_BMW_-Serie_5.jpgㄹhttps://upload.wikimedia.org/wikipedia/commons/b/bf/2018_BMW_520d_M_Sport_Automatic_2.0_%281%29.jpg", 10, "Luxury, High performance, Advanced safety, Spacious, Tech-savvy", 
     "The 2018 BMW 5 Series is a luxury sedan that combines high performance with sophisticated features, catering to drivers who value both comfort and speed.", "RWD"),

    ("Audi", "Q7", 2020, "SUV", 25000, "Automatic", 4, "In Repair", "No", "https://images.ctfassets.net/c9t6u0qhbv9e/2020AudiQ7TestDriveReviewsummary/9f9d5d4a0d9e7c0618a8d74039b4a2b8/2020_Audi_Q7_Test_Drive_Review_summaryImage.jpegㄹhttps://www.edmunds.com/assets/m/audi/q7/2020/oem/2020_audi_q7_4dr-suv_prestige-55-tfsi-quattro_fq_oem_1_600.jpgㄹhttps://images.cars.com/cldstatic/wp-content/uploads/audi-q7-2020-4-badge--exterior--front--grile--outdoors--white.jpg", 11, "Luxurious, Spacious, Advanced safety, Family-friendly, Powerful engine", 
     "The 2020 Audi Q7 is a luxury SUV with a spacious interior and premium features, ideal for families seeking comfort and style.", "AWD"),

    ("Tesla", "Model X", 2019, "SUV", 20000, "Automatic", 4, "Operational", "Yes", "https://vehicle-images.dealerinspire.com/5466-110008891/5YJXCDE29KF180249/c717eb0a96b5afd22cd3822da7ca126d.jpgㄹhttps://static.overfuel.com/photos/178/184814/image-1.webpㄹhttps://www.edmunds.com/assets/m/tesla/model-x/2019/oem/2019_tesla_model-x_4dr-suv_performance_fq_oem_1_600.jpg", 12, "Electric, High-tech features, Fast acceleration, Spacious, Safe",
     "The 2019 Tesla Model X is an electric SUV with advanced technology and impressive acceleration, perfect for those who want an eco-friendly and innovative vehicle.", "AWD"),

    ("DMC", "DeLorean", 1981, "Coupe", 50000, "Manual", 2, "Operational", "Yes", "https://www.motortrend.com/uploads/2023/10/005-back-to-the-future-delorean-facts-7.jpg?w=768&width=768&q=75&format=webpㄹhttps://images.hgmsites.net/hug/back-to-the-future-delorean-time-machine-replica-photo-by-charitybuzz_100786353_h.jpgㄹhttps://www.americanmusclecarmuseum.com/files/cars/1980-delorean-dmc-12_7681.jpg", 12, "Iconic design, Gull-wing doors, Stainless steel body, Time machine, Classic",
     "The 1981 DeLorean DMC-12 is an iconic sports car known for its gull-wing doors and stainless steel body. It gained fame as the time machine in the Back to the Future movies.", "RWD"),
    
    ("Subaru", "Forester", 1998, "SUV", 200000, "Automatic", 4, "In Repair", "No", "https://www.texasjdm.com/wp-content/uploads/2023/10/DSC07911.jpgㄹhttps://www.subaruforester.org/attachments/myfozzy-jpg.579562/ㄹhttps://i.pinimg.com/originals/1d/9a/71/1d9a7119e96e11dc8e53ce187fd1ebdd.jpg", 11, "All-wheel drive, Reliable, Spacious, Adventure-ready, Long-lasting",
     "The 1998 Subaru Forester is a rugged SUV with all-wheel drive and a reputation for reliability. A versatile vehicle that is ready for outdoor adventures.", "AWD"),
    
    ("Chevrolet", "Silverado", 1989, "Truck", 300000, "Automatic", 2, "Operational", "Yes", "https://cdn11.bigcommerce.com/s-rnmf5r1skr/images/stencil/1000x649/VehicleImages/1989ChevroletC1500.jpgㄹhttps://bringatrailer.com/wp-content/uploads/2022/09/1989_chevrolet_c1500_20211031_095914-45976.jpgㄹhttps://cdn.dealeraccelerate.com/raleigh/8/1544/36606/1920x1440/1989-chevrolet-k-1500", 12, "Durable, High payload, Classic design, Reliable, Workhorse",
     "The 1989 Chevrolet Silverado is a classic pickup truck known for its durability and high payload capacity. A reliable workhorse that has stood the test of time.", "4WD")
    
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

    # Insert data into the Vehicles table with ServiceID, KeyFeatures, Description, and DriveTrain
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for make, model, year, type_, mileage, transmission, num_doors, repair_status, available, photos, location_id, key_features, description, drivetrain in vehicle_data:
        service_id = determine_service_id(mileage)
        cursor.execute(
            "INSERT INTO Vehicles (VehicleID, Make, Model, Year, Type, Mileage, Transmission, NumDoors, RepairStatus, Available, Photos, LocationID, ServiceID, KeyFeatures, Description, DriveTrain) "
            "VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (make, model, year, type_, mileage, transmission, num_doors, repair_status, available, photos, location_id, service_id, key_features, description, drivetrain)
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
    #insert_locations_data()
    insert_vehicle_data()
    #insert_service_intervals_data()


if __name__ == "__main__":
    main()

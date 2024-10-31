from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from markupsafe import Markup
import hashlib

app = Flask(__name__)
app.secret_key = 'super secret key'

# Path to the database file (The database used is SQLite and is stored in the same directory as the flask app).
db_path = 'car_rental.db'


@app.route("/")
def index():
    return render_template("login.html")

@app.route("/products", methods=['GET'])
def products():
    vehicle_data = get_vehicle_information()
    vehicle_html = ""
    for vehicle in vehicle_data:
        vehicle_html += Markup("""   <div class="col">
                                        <div><img class="rounded img-fluid d-block w-100 fit-cover" style="height: 400px;width: 400px !important;" src="https://encrypted-tbn3.gstatic.com/shopping?q=tbn:ANd9GcQ4xKI2ZyxrU7kamYTQFunkQK1qMz_EN6PUCzxAf04RSRiOYuBSx7JYlaDdw68eQCRN747xuCjl_oN3LVTxQU8Dpp1rRlAvJjPbsVSCgpFcu8HFpN1YhfgP">
                                            <div class="py-4">
                                                <h4>0000 Make Model</h4>
                                            </div>
                                        </div>
                                    </div>""")

    return render_template("products.html", vehicle_html=vehicle_html)

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
    pass

def get_vehicle_information():
    return [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

def update_vehicle_information(vehicleID):
    pass


# Uncomment the docstring only when you specifically want to load users into database
"""@app.route("/test")
def run_test():
    create_user("Taylor J. Brown", "313 Youngberry St. Fayetteville, NC 28314", 9168737714, "tbrown145@broncos.uncfsu.edu", 27, "M", "Test123abc")
    create_user("Admin", "123 ABC St. Fayetteville, NC 28314", 9105554545, "admin@admin.com", 99, "M", "Test123abc", 1)
    return redirect(url_for("index"))"""

if __name__ == '__main__':
    app.run(debug=True)
    
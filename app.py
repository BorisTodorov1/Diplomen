from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'


db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='admin',
    database='car_parts_db',
    connect_timeout=120
)
cursor = db.cursor()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            stored_password = user[2]  
            if password == stored_password:
                session['user_id'] = user[0]  
                if user[3] == 'admin':  
                    
                    print("Admin login successful")  
                    return redirect(url_for('admin_dashboard'))
                else:
                    
                    print("Customer login successful")  
                    return redirect(url_for('customer_dashboard'))
            else:
                print("Invalid password") 
        else:
            print("User not found")  

        
        flash('Invalid email or password')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            flash('Email already registered')
            return redirect(url_for('register'))


        cursor.execute("INSERT INTO Users (email, password, role) VALUES (%s, %s, %s)", (email, password, 'customer'))
        db.commit()

        flash('Registration successful')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/admin/dashboard')
def admin_dashboard():

    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT role FROM Users WHERE id = %s", (user_id,))
        user_role = cursor.fetchone()[0]
        if user_role == 'admin':

            return render_template('admin-dashboard.html')
    

    return redirect(url_for('login'))


@app.route('/customer_dashboard')
def customer_dashboard():
    cursor.execute("SELECT * FROM carparts")
    car_parts = cursor.fetchall()
    return render_template('customer-dasboard.html', car_parts=car_parts)


@app.route('/add_part', methods=['POST'])
def add_part():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        quantity = request.form['quantity']
        price = request.form['price']


        cursor.execute("INSERT INTO carparts (name, description, quantity, price) VALUES (%s, %s, %s, %s)", (name, description, quantity, price))
        db.commit()

        flash('Part added successfully')
        return redirect(url_for('admin_dashboard'))


@app.route('/logout')
def logout():

    session.pop('user_id', None)  
    flash('Logged out successfully')
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)

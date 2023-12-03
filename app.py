from flask import Flask, abort, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__,)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:admin@localhost/autohub'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100))
    role = db.Column(db.Enum('Customer', 'Admin', 'Employee', 'Courier'), nullable=False)
    current_order_id = db.Column(db.Integer)
    orders = db.relationship('Order', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    order_time = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    delivery_time = db.Column(db.TIMESTAMP)
    deliver_location = db.Column(db.String(100))
    products = db.relationship('Product', secondary='order_products', backref='orders')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    definition = db.Column(db.String(50))
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100))
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

order_products = db.Table('order_products',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)


@app.route('/')
def home():
    return render_template('index.html')

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
    return dict(User=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session['user_id'] = user.id
            if user.role == 'admin':
                print("Admin login successful")
                return redirect(url_for('admin_dashboard'))
            else:
                print("Customer login successful")
                return redirect(url_for('customer_dashboard'))
        else:
            print("Invalid email or password")
            flash('Invalid email or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered')
            return redirect(url_for('register'))

        new_user = User( email=email, password=password, role='customer')
        new_user = User(username=request.form['username'], email=email, password=password, role='customer')
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        user_role = User.query.get(user_id).role
        if user_role == 'admin':
            products = Product.query.all()
            categories = Category.query.all()
            customers = User.query.filter_by(role='customer').all()
            orders = Order.query.all()
            return render_template('admin-dashboard.html', products=products, categories=categories, customers=customers, orders=orders)
        else:
            abort(403) 

    return redirect(url_for('login'))

@app.route('/admin/add_category', methods=['POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        definition = request.form['definition']

        new_category = Category(name=name, definition=definition)
        db.session.add(new_category)
        db.session.commit()

        flash('Category added successfully')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_customer/<int:user_id>', methods=['GET'])
def delete_customer(user_id):
    customer = User.query.get(user_id)
    if customer:
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully')
    return redirect(url_for('admin_dashboard'))

# Routes for Employee
@app.route('/employee/dashboard')
def employee_dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        user_role = User.query.get(user_id).role
        if user_role == 'employee':
            products = Product.query.all()
            return render_template('employee-dashboard.html', products=products)

    return redirect(url_for('login'))

# Routes for Courier
@app.route('/courier/dashboard')
def courier_dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        user_role = User.query.get(user_id).role
        if user_role == 'courier':
            orders = Order.query.all()
            return render_template('courier-dashboard.html', orders=orders)

    return redirect(url_for('login'))

@app.route('/courier/choose_vehicle/<int:order_id>', methods=['POST'])
def choose_vehicle(order_id):
    if request.method == 'POST':
        order = Order.query.get(order_id)
        if order:
            quantity = sum(product.quantity for product in order.products)
            if quantity > 10:
                vehicle = 'van'
            else:
                vehicle = 'car'

            order.vehicle = vehicle
            db.session.commit()

            flash('Vehicle chosen successfully')
    return redirect(url_for('courier_dashboard'))

@app.route('/customer_dashboard')
def customer_dashboard():
    car_parts = Product.query.all()
    return render_template('customer-dashboard.html', car_parts=car_parts)

@app.route('/addpart', methods=['GET', 'POST'])
def add_part():
    if request.method == 'POST':
        # Process the form data and add the part to the database
        name = request.form['name']
        description = request.form['description']
        quantity = request.form['quantity']
        price = request.form['price']

        new_part = Product(name=name, description=description, quantity=quantity, price=price)
        db.session.add(new_part)
        db.session.commit()

        flash('Part added successfully')
        return redirect(url_for('admin_dashboard'))

    # If it's a GET request, render the 'add_part.html' template
    return render_template('add-part.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

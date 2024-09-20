from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection
client = MongoClient("mongodb+srv://xZephy:Rafikul8910@cluster0.ciofglz.mongodb.net/")
db = client["vagos_db"]
products_collection = db["vagos_products"]
orders_collection = db["vagos_orders"]
users_collection = db["vagos_users"]

products = [
    {"name": "Combat Pistol", "price": 150000, "image_url": "https://i.ibb.co/rxx2fzJ/2.png"},
    {"name": "Ammo Pistol", "price": 5000, "image_url": "https://i.ibb.co/9cvZsCJ/3.png"},
    {"name": "Mini SMG", "price": 300000, "image_url": "https://i.ibb.co/S0GPQdR/4.png"},
    {"name": "Ammo SMG", "price": 8000, "image_url": "https://i.ibb.co/5YNpnwV/5.png"},
    {"name": "Armor", "price": 10000, "image_url": "https://i.ibb.co/7GfcGWv/6.png"},
    {"name": "Handcuff + Key", "price": 20000, "image_url": "https://i.ibb.co/WP09CGt/7.png"},
    {"name": "Oxy", "price": 2000, "image_url": "https://i.ibb.co/cbvWj2V/8.png"}
]


@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    active_order = orders_collection.find_one({"name_in_city": session['user'], "status": {"$in": ["pending", "paid"]}})

    if active_order:
        return render_template('current_order.html', order=active_order)

    return render_template('index.html', products=products)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name_in_city = request.form['name_in_city']
        password = request.form['password']
        user = users_collection.find_one({"name_in_city": name_in_city, "password": password})

        if user:
            session['user'] = name_in_city
            return redirect(url_for('index'))
        else:
            error = "Invalid credentials. Please try again."
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/order', methods=['POST'])
def order():
    if 'user' not in session:
        return redirect(url_for('login'))

    name_in_city = session['user']
    order_items = []

    for product in products:
        quantity = int(request.form.get(f'quantity_{product["name"]}', 0))
        if quantity > 0:
            order_items.append({
                "name": product["name"],
                "quantity": quantity,
                "price": product["price"],
                "total_price": quantity * product["price"]
            })

    if order_items:
        total_price = sum(item["total_price"] for item in order_items)
        orders_collection.insert_one({
            "name_in_city": name_in_city,
            "order_items": order_items,
            "total_price": total_price,
            "status": "pending"
        })
        return redirect(url_for('index'))

    return redirect(url_for('index'))


@app.route('/admin34')
def admin():
    orders = list(orders_collection.find())
    users = list(users_collection.find())
    return render_template('admin.html', orders=orders, users=users)


@app.route('/admin/update_status/<order_id>', methods=['POST'])
def update_status(order_id):
    status = request.form['status']
    if status == "delivered":
        orders_collection.delete_one({"_id": ObjectId(order_id)})
    else:
        orders_collection.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": status}})
    return redirect(url_for('admin'))


@app.route('/admin/add_user', methods=['POST'])
def add_user():
    name_in_city = request.form['name_in_city']
    password = request.form['password']
    users_collection.insert_one({"name_in_city": name_in_city, "password": password})
    return redirect(url_for('admin'))


@app.route('/logout')
def user_logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/delete_order', methods=['POST'])
def delete_order():
    if 'user' in session:
        order = orders_collection.find_one({"name_in_city": session['user'], "status": "pending"})
        if order:
            orders_collection.delete_one({"_id": ObjectId(order["_id"])})
        return redirect(url_for('index'))
    return redirect(url_for('login'))


# For Vercel deployment, do not use the __main__ block
app = app

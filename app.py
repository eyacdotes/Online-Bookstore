from flask import Flask,request,render_template,url_for,redirect,flash,g,session
from dbhelper import *
from datetime import datetime
import math
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure the upload folder
app.config['UPLOAD_FOLDER'] = 'static/images/product_img'

# Optionally, you can set a maximum file size for uploads (in bytes)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

customerHeader = ['id','name','email','address','actions']
itemHeader = ['isbn','title','author', 'genre', 'price', 'type', 'quantity', 'actions'] 

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
    #response.cache_control.no_store = True
    #return response

def calculate_total_pages(total_items):
    return math.ceil(total_items / 15)
    
@app.route('/', methods=['GET','POST'])
def index():
    if 'user' in session:
        if session['user'][3] == 'admin':
            total_customer = countall('customer')
            total_items = countall('items')
            total_orders = countall('orders')
            recent_orders = get_recent_orders()
            print("Recent Orders")
            print(recent_orders)
            recent_customer = get_recent('customer', 'c_id')
            recent_items = get_recent('items', 'i_id')
            #print(recent_items)
            return render_template("admin_dashboard.html", title="Admin Dashboard", ttl_ord = total_orders, ttl_cust = total_customer, ttl_item=total_items, rec_ord = recent_orders, rec_item=recent_items, rec_cust=recent_customer, user=session['user'])
        else:
            if session['user'][4] != 0:
                data = []
                try:
                    data = getall('items', page = 1)
                except Exception as e:
                    flash("NO ITEMS AVAILBLE")
                return render_template("shop.html", title="BookShop", search=False, items=data, user=session['user'])
            else:
                return render_template("error.html", message="Your account is deactivated please contact admin support!")
            
    if request.method == 'POST':
        session.pop('user', None)
        
        uname=request.form['username']
        passw=request.form['password']
        
        account = []
        account = getrecord('users', username=uname.replace('\\', '').replace('/', '').replace('*', '').replace('-', '').lower(), password=passw)
        
        if len(account) > 0:
            session['user'] = account[0]
            if session['user'][3] == 'admin':
                total_customer = countall('customer')
                total_items = countall('items')
                total_orders = countall('orders')
                recent_orders = get_recent_orders()
                recent_customer = get_recent('customer', 'c_id')
                recent_items = get_recent('items', 'i_id')
                return render_template("admin_dashboard.html", title="Admin Dashboard", ttl_ord = total_orders, ttl_cust = total_customer, ttl_item=total_items, rec_ord = recent_orders, rec_item=recent_items, rec_cust=recent_customer, user=session['user'])
            else:
                if session['user'][4] != 0:
                    data = []
                    try:
                        data = getall('items', page = 1)
                    except Exception as e:
                        flash("NO ITEMS AVAILBLE")
                    return render_template("shop.html", title="BookShop", search=False, items=data, user=session['user'])
                else:
                    return render_template("error.html", message="Your account is deactivated please contact admin support!")
        else:
            flash("Invalid username or password")
    return render_template('login.html', title="Sign in")
    
@app.before_request
def before_request():
    g.user = None
    
    if 'user' in session:
        g.user = session['user']
        
@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return redirect(url_for('index'))

#####################
#   CUSTOMER LOGIN  #
#####################
"""
@app.route('/items-list')
def items_list():
    if 'user' in session:
        print(session['user'])
        if session['user'][3] == 'customer':
            return render_template("shop.html", user=session['user'][1])
        else:
            return render_template('login.html')
    return redirect(url_for('customer'))
"""

@app.route('/register')
def register_page():
    if 'user' in session:
        return redirect(url_for('index'))
    else:
        return render_template('register.html')

@app.route('/account-created-successfully')
def successfully_page():
    if 'user' in session:
        return redirect(url_for('index'))
    else:
        return render_template('success.html')

@app.route('/cart')
def cart_page():
    if 'user' in session:
        if session['user'][3] == 'customer':
            data = getcartitems(session['user'][0])
            data2 = gettotalprice(session['user'][0])
            print(data)
            return render_template("cart.html", title="Your Cart", items=data, totalprice=data2, user=session['user'])
    return redirect(url_for('index'))

@app.route('/add-to-cart', methods = ['POST'])
def add_to_cart():
    if 'user' in session:
        if session['user'][3] == 'customer':
            if request.method == "POST":
                c_id = request.form['c_id']
                i_id = request.form['i_id']
                qty = request.form['qty']
                
                data = getcartitems(session['user'][0])
                
                flag = False
                
                if len(data) > 0:
                    print(f"I ID: {i_id}")
                    for item in data:
                        print(item[8])
                        if int(i_id) == int(item[8]):
                            total = int(item[2]) + int(qty)
                            print(f"TOTAL: {total}")
                            if total > int(item[9]):
                                success = updatecartitem(item[9], item[3])
                            else:
                                success = updatecartitem(total, item[3])
                            flag = True
                    print(f"CART: {data}")
                    
                if not flag:
                    success = addrecord('itemsordered',c_id=c_id, i_id=i_id, qty=qty, status='1')
                flash("Item added to cart successfully!") if success else flash("Add to cart failed!")
                #return render_template('login.html')
    return redirect(url_for('index'))
    
@app.route('/edit-cart-item', methods = ['POST'])
def edit_cart_item():
    if 'user' in session:
        if session['user'][3] == 'customer':
            if request.method == "POST":
                io_id = request.form['io_id']
                qty = request.form['qty']
                success = updatecartitem(qty, io_id)
                if success:
                    flash("Cart updated successfully!")
                return redirect(url_for('cart_page'))
                
    return redirect(url_for('index'))
    
@app.route('/delete-cart-item/<int:id_data>', methods=['POST', 'GET'])
def delete_cart_item(id_data):
    if 'user' in session:
        if session['user'][3] == 'customer':
            success = deletecartitem(id_data)
            return redirect(url_for('cart_page'))
    return redirect(url_for('index'))
    
@app.route('/search', methods=['POST'])
def customer_search_item():
    if 'user' in session:
        if session['user'][3] == 'customer':
            search_text = request.form.get('search_text')  # Get the search text from the form
            if search_text == "":
                flash("Please type something to search!")
                return redirect(url_for('index'))
            else:
                data = getitems('items', i_id=search_text, isbn=search_text, title=search_text, author=search_text, price=search_text, i_type=search_text, genre=search_text)
                if len(data) == 0:
                    flash(f"No matches with {search_text}")
                    return redirect(url_for('index'))
                else:
                    flash(f"{len(data)} items matches with {search_text}")
                    return render_template("shop.html", title="BookShop", search=True, items=data, user=session['user'])
    return redirect(url_for('index'))
    
@app.route('/place-order', methods=['POST'])
def place_order():
    if 'user' in session:
        if session['user'][3] == 'customer':
            data = getcartitems(session['user'][0])
            data2 = gettotalprice(session['user'][0])
            print()
            print("CART ITEMS:")
            print(data)
            print()
            print("TOTAL")
            print(data2)
            
            print()
            print()
            print(f"MAX: {getmax()}")
            
            
            o_id = str(getmax() + 1)
            o_date = request.form.get('date')
            print(f"DATE: {o_date}")
            ship_address = getaddress(session['user'][0])
            c_id = session['user'][0]
            print(f"ADDRESS: {ship_address}")
            
            
            for items in data:
                print(f"ITEM: {items}")
                stock = getstock(items[8])
                print("STOCK: ", stock[0][0])
                if int(items[2]) <= int(stock[0][0]):
                    io_id = items[3]
                    success = addrecord('orders', o_id=o_id, o_date=o_date, ship_address=ship_address, c_id=c_id, io_id=io_id, status="Pending")
                    deleted = deleterecord('itemsordered', io_id=io_id)
                    #remove_item = deleterecord('items', i_id=items[8])
                    update_stock = updatestockitem(items[2],items[8])
                else:
                    flash("Failed to place order. your item quantity exceeds the stock.")
                    print("Order Failed!")
                    return redirect(url_for('cart_page'))
            return redirect(url_for('index'))
    return redirect(url_for('index'))
    
@app.route('/orders')
def orders_page():
    if 'user' in session:
        if session['user'][3] == 'customer':
            orders = getorders(session['user'][0])
            print(orders)
            merged_orders = {}

            for order in orders:
                order_id = order[0]
                if order_id in merged_orders:
                    merged_orders[order_id]['orders'].append(order)
                    merged_orders[order_id]['total_price'] += order[3] * order[4]
                else:
                    merged_orders[order_id] = {'orders': [order], 'total_price': order[3] * order[4], 'date_ordered': order[1], 'status': order[5]}

            data = list(merged_orders.values())
            
            return render_template("orders.html", title="Your Orders", items=data, user=session['user'])
    return redirect(url_for('index'))
    
@app.route('/create-account', methods = ['POST'])
def create_account():
    if 'user' in session:
        return redirect(url_for('index'))
    else:
        if request.method == "POST":
            try:
                name = request.form['name']
                email = request.form['username']
                address = request.form['address']
                password = request.form['password']
                
                success = addrecord('users',username=email.replace('\\', '').replace('/', '').replace('*', '').replace('-', '').lower(), password=password, u_type='customer', status=1)
                
                if not success:
                    flash("Email already in use. Please login!")
                    return redirect(url_for('register_page'))
                else:
                    c_id = getrecord('users', username=email)
                    print(c_id)
                    success = addrecord('customer',c_id=c_id[0][0], c_name=name.title(), c_email=email.lower(), c_address=address.title(), status=1)
                    date_now = datetime.now().date()
                    cart_created = addrecord('cart',cart_id=c_id[0][0], date_created=date_now)
                    print(f"CART CREATED? {cart_created}")
                    print(f"DATE? {date_now}")
                    return redirect(url_for('successfully_page'))
            except Exception as e:
                flash("Email already in use. Please choose another or log in.")
                return redirect(url_for('register_page'))
        return render_template('register.html')

    
#####################
#   CUSTOMER CODE   #
#####################
@app.route('/customers')
def customer():
    if 'user' in session:
        if session['user'][3] == 'admin':
            data = []
            try:
                data = getall('customer', page=0)
            except Exception as e:
                return redirect(url_for('customer'))
            if len(data) == 0:
                flash("Customer list is empty!")
            return render_template("admin_customers.html", customer=data, user=session['user'], title="Customers List", header=customerHeader)
    return redirect(url_for('index'))
 
@app.route('/insert-customer', methods = ['POST'])
def insertCustomer():
    if 'user' in session:
        if request.method == "POST":
            name = request.form['name']
            email = request.form['email']
            address = request.form['address']
            password = request.form['password']
            #####
            success = addrecord('users',username=email.lower(), password=password, u_type='customer', status=1)            
            if not success:
                flash("Failed to add customer email is already in use")
                totalpages = calculate_total_pages(countall('customer'))
                return redirect(url_for('customer'))
            else:
                c_id = getrecord('users', username=email)
                success = addrecord('customer',c_id=c_id[0][0], c_name=name.title(), c_email=email.lower(), c_address=address.title(), status=1)
            #####
            
            flash("Failed to add customer email is already in use") if not success else flash("Customer added successfully")
            totalpages = calculate_total_pages(countall('customer'))
            return redirect(url_for('customer'))
    return render_template('login.html')
        
@app.route('/update-customer', methods = ['POST'])
def updateCustomer():
    if 'user' in session:
        if request.method == 'POST':
            id_data = request.form['id']
            name = request.form['name']
            email = request.form['email']
            address = request.form['address']
            success = updaterecord('customer',c_id=id_data, c_name=name, c_email=email, c_address=address)
            flash("Customer updated successfully!") if success else flash("No changes have been made!")
            return redirect(url_for('customer'))
    return render_template('login.html')
    
@app.route('/delete-customer/<string:id_data>', methods = ['POST', 'GET'])
def deleteCustomer(id_data):
    if 'user' in session:
        success = deleterecord('users', u_id=id_data)
        success = deleterecord('customer', c_id=id_data)
        flash("Customer deleted successfully!") if success else flash("Failed to delete customer!")
        return redirect(url_for('customer'))
    return render_template('login.html')

@app.route('/search-customer', methods=['POST'])
def searchCustomer():
    if 'user' in session:
        if session['user'][3] == 'admin':
            search_text = request.form.get('search_text')  # Get the search text from the form
            if search_text == "":
                flash("Please type something to search!")
                return redirect(url_for('customer'))
            else:
                data = getrecord('customer', c_id=search_text, c_name=search_text, c_email=search_text, c_address=search_text)
                if len(data) == 0:
                    flash(f"No record matches with {search_text}")
                    return redirect(url_for('customer'))
                else:
                    #flash(f"No record matches with {search_text}") if len(data)==0 else flash(f"{len(data)} record matches")
                    flash(f"{len(data)} record matches")
                    return render_template("admin_customers.html", title="Customers List", user=session['user'], customer=data, header=customerHeader)
    return render_template('login.html')
    
######################
#     ITEMS CODE     #
######################
@app.route('/items')
def items():
    if 'user' in session:
        if session['user'][3] == 'admin':
            data = []
            try:
                data = getall('items', page=0)
                print(data)
            except Exception as e:
                return redirect(url_for('items'))
            if len(data) == 0:
                flash("Items list is empty!")
            return render_template("admin_items.html", data=data, title="Items List", user=session['user'], header=itemHeader)
    return redirect(url_for('index'))

@app.route('/insert-item', methods = ['POST'])
def insertItem():
    if 'user' in session:
        if request.method == "POST":
            isbn = request.form['isbn']
            title = request.form['title']
            author = request.form['author']
            genre = request.form['genre']
            price = request.form['price']
            itype = request.form['itype']
            stock = request.form['stocks']
            
            success = addrecord('items',isbn=isbn, title=title.title(), author=author.title(), genre=genre.title(), price=price, i_type=itype, stock=stock, status=1, img="none")
            flash("Item added successfully!") if success else flash("Failed to add item ISBN must be unique!")
            totalpages = calculate_total_pages(countall('items'))
            return redirect(url_for('items'))
    return render_template('login.html')
    
@app.route('/update-item', methods = ['POST'])
def updateItem():
    if 'user' in session:
        if request.method == 'POST':
            id_data = request.form['id']
            isbn = request.form['isbn']
            title = request.form['title']
            author = request.form['author']
            genre = request.form['genre']
            price = request.form['price']
            itype = request.form['itype']
            stock = request.form['stocks']
            
            success = updaterecord('items',i_id=id_data, isbn=isbn.title(), title=title.title(), author=author.title(), genre=genre.title(), price=price, i_type=itype, stock=stock)
            flash("Item updated successfully!") if success else flash("No changes have been made!")
            return redirect(url_for('items'))
    return render_template('login.html')
    
@app.route('/delete-item/<string:id_data>', methods = ['POST', 'GET'])
def deleteItem(id_data):
    if 'user' in session:
        success = deleterecord('items', i_id=id_data)
        flash("Item deleted successfully!") if success else flash("Failed to delete item!")
        return redirect(url_for('items'))
    return render_template('login.html')
    
@app.route('/search-item', methods=['POST'])
def searchItem():
    if 'user' in session:
        if session['user'][3] == 'admin':
            search_text = request.form.get('search_text')  # Get the search text from the form
            if search_text == "":
                flash("Please type something to search!")
                return redirect(url_for('items'))
            else:
                data = getrecord('items', isbn=search_text, title=search_text, author=search_text, price=search_text, i_type=search_text, genre=search_text, stock=search_text)
                if len(data) == 0:
                    flash(f"No record matches with {search_text}")
                    return redirect(url_for('items'))
                else:
                    flash(f"No record matches with {search_text}") if len(data)==0 else flash(f"{len(data)} record matches")
                    return render_template("admin_items.html", user=session['user'], data=data, page=1, totalpages=1, prev_page=None, next_page=None, title="Items List", header=itemHeader)
    return render_template('login.html')

######################
#     ORDERS CODE     #
######################
@app.route('/orders-list')
def orders():
    if 'user' in session:
        if session['user'][3] == 'admin':
            data = []
            try:
                data = getall('orders', page = 0)
                print("Data 1:")
                print(data)
                
                data2 = get_all_orders()
                print("Data 2:")
                print(data2)
            except Exception as e:
                return redirect(url_for('orders'))
            if len(data) == 0:
                flash("Orders list is empty!")
            return render_template("admin_orders.html", orders=data, data2=data2, title="Orders List", user=session['user'])
    return redirect(url_for('index'))
    
@app.route('/update-order-status', methods = ['POST'])
def updateOrderStatus():
    if 'user' in session:   
        if request.method == 'POST':
            id_data = request.form['id']
            status = request.form['status']
            success = updaterecord('orders',o_id=id_data, status=status)
            flash("Order status updated successfully!") if success else flash("No changes have been made!")
            return redirect(url_for('orders'))
            
    return redirect(url_for('index'))

if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=5000)
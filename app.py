import secrets
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import mysql.connector
import bcrypt
import requests
import os

app = Flask(__name__)
if not os.environ.get('FLASK_SECRET_KEY'):
    os.environ['FLASK_SECRET_KEY'] = secrets.token_hex(16)

app.secret_key = os.environ.get('FLASK_SECRET_KEY')

db_host = os.environ.get('DB_HOST', 'shopNA.mysql.pythonanywhere-services.com')
db_user = os.environ.get('DB_USER', 'shopNA')
db_password = os.environ.get('DB_PASSWORD', 'password000')
db_database = os.environ.get('DB_DATABASE','shopNA$back')

db_config = {
    'host': 'shopNA.mysql.pythonanywhere-services.com',
    'user': 'shopNA',
    'password': 'password000',
    'database': 'shopNA$back',
    'auth_plugin': 'mysql_native_password'
}

@app.route('/')
def test():
    return redirect(url_for('signin'))

@app.route('/home')
def home():
    if 'email' in session:
        if session['email'] == 'admin@mail.com':
            return redirect(url_for('admin_panel'))
        # else:
        cart_count = get_cart_count()
        return render_template('index.html', cart_count=cart_count)
    # else:
    return redirect(url_for('signin'))


@app.route('/admin', methods=['GET'])
def admin_panel():
    if 'email' in session and session['email'] == 'admin@mail.com':
        return render_template('admin_panel.html')
    # else:
    return redirect(url_for('signin'))


@app.route('/recipe')
def recipe():
    cart_count = get_cart_count()
    return render_template('recipe.html', cart_count=cart_count)

@app.route('/products')
def products():
    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()
    curs.execute("SELECT * FROM Product")
    products = curs.fetchall()
    curs.close()
    conn.close()
    cart_count = get_cart_count()
    return render_template('shop.html', products=products, cart_count=cart_count)

def get_cart_count():
    if 'email' in session:
        conn = mysql.connector.connect(**db_config)
        curs = conn.cursor()
        select_query = """
        SELECT COUNT(CP.ProductId)
        FROM CartProduct CP
        JOIN Cart C ON CP.CartId = C.Id
        JOIN User U ON C.UserId = U.Id
        WHERE U.Email = %s
        """
        curs.execute(select_query, (session['email'],))
        cart_count = curs.fetchone()[0]
        curs.close()
        conn.close()
        return cart_count
    pass

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = mysql.connector.connect(**db_config)
        curs = conn.cursor()
        try:
            select_query = "SELECT * FROM User WHERE Email = %s"
            curs.execute(select_query, (email,))
            existing_user = curs.fetchone()
            if existing_user:
                error_message = 'Email already exists. Please choose a different email.'
                return render_template('signup.html', error_message=error_message)
            # else:
            insert_query = "INSERT INTO User (Name, Email, Password, Phone) VALUES (%s, %s, %s, %s)"
            user_data = (name, email, hashed_password.decode('utf-8'), phone)
            curs.execute(insert_query, user_data)
            conn.commit()
        finally:
            curs.close()
            conn.close()
        session['email'] = email
        return redirect(url_for('profile'))
    # else:
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = mysql.connector.connect(**db_config)
        curs = conn.cursor()
        try:
            query = "SELECT Password FROM User WHERE Email = %s"
            curs.execute(query, (email,))
            result = curs.fetchone()
            print(result)
            if result:
                hashed_password = result[0]
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                    session['email'] = email
                    return redirect(url_for('home'))
            return render_template('signup.html')
        finally:
            curs.close()
            conn.close()
    if 'email' in session:
        return redirect(url_for('home'))
    return render_template('signin.html')

@app.route('/profile')
def profile():
    if 'email' in session:
        conn = mysql.connector.connect(**db_config)
        curs = conn.cursor()
        curs.execute("SELECT * FROM User WHERE Email = %s", (session['email'],))
        user = curs.fetchone()
        select_shipping_query = """
        SELECT * FROM Shipping
        INNER JOIN User ON Shipping.UserId = User.Id
        WHERE User.Email = %s
        """
        curs.execute(select_shipping_query, (session['email'],))
        shipping_info = curs.fetchall()
        curs.close()
        conn.close()
        cart_count = get_cart_count()
        return render_template('profile.html', user=user, shipping_info=shipping_info, cart_count=cart_count)
    # else:
    return redirect(url_for('signin'))

@app.route('/signout')
def signout():
    session.clear()
    return redirect(url_for('signin'))

@app.route('/search')
def search():
    query = request.args.get('query')
    if not query or query.strip() == '':
        return redirect(url_for('products'))
    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()
    search_query = "SELECT * FROM Product WHERE Name LIKE %s OR Description LIKE %s"
    pattern = f'%{query}%'
    curs.execute(search_query, (pattern, pattern))
    products = curs.fetchall()
    curs.close()
    conn.close()
    cart_count = get_cart_count()
    return render_template('search_results.html', products=products, query=query, cart_count=cart_count)

@app.route('/cart')
def cart():
    if 'email' not in session:
        return redirect(url_for('signin'))
    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()
    try:
        select_query = """
        SELECT P.Id, P.Name, P.Description, P.Price, P.Image, P.Category
        FROM CartProduct CP
        JOIN Product P ON CP.ProductId = P.Id
        JOIN Cart C ON CP.CartId = C.Id
        JOIN User U ON C.UserId = U.Id
        WHERE U.Email = %s
        """
        curs.execute(select_query, (session['email'],))
        cart_products = curs.fetchall()
        total_query = """
        SELECT SUM(P.Price)
        FROM CartProduct CP
        JOIN Product P ON CP.ProductId = P.Id
        JOIN Cart C ON CP.CartId = C.Id
        JOIN User U ON C.UserId = U.Id
        WHERE U.Email = %s
        """
        curs.execute(total_query, (session['email'],))
        total_price = curs.fetchone()[0]
        select_shipping_query = """
        SELECT * FROM Shipping
        INNER JOIN User ON Shipping.UserId = User.Id
        WHERE User.Email = %s
        """
        curs.execute(select_shipping_query, (session['email'],))
        shipping_info = curs.fetchall()
    finally:
        curs.close()
        conn.close()
    return render_template('cart.html', cart_products=cart_products, total_price=total_price, shipping_info=shipping_info)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'email' not in session:
        return redirect(url_for('signin'))
    product_id = request.form.get('product_id')
    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()
    select_cart_query = "SELECT Id FROM Cart WHERE UserId = (SELECT Id FROM User WHERE Email = %s)"
    curs.execute(select_cart_query, (session['email'],))
    cart_row = curs.fetchone()
    if cart_row:
        cart_id = cart_row[0]
    else:
        insert_cart_query = "INSERT INTO Cart (UserId) SELECT Id FROM User WHERE Email = %s"
        curs.execute(insert_cart_query, (session['email'],))
        conn.commit()
        cart_id = curs.lastrowid
    insert_cart_product_query = "INSERT INTO CartProduct (CartId, ProductId) VALUES (%s, %s)"
    cart_product_data = (cart_id, product_id)
    curs.execute(insert_cart_product_query, cart_product_data)
    conn.commit()
    curs.close()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'email' not in session:
        return redirect(url_for('signin'))
    product_id = request.form.get('product_id')
    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()
    select_cart_query = "SELECT Id FROM Cart WHERE UserId = (SELECT Id FROM User WHERE Email = %s)"
    curs.execute(select_cart_query, (session['email'],))
    cart_id = curs.fetchone()[0]
    delete_query = "DELETE FROM CartProduct WHERE CartId = %s AND ProductId = %s"
    curs.execute(delete_query, (cart_id, product_id))
    conn.commit()
    curs.close()
    conn.close()
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'email' not in session:
        return redirect(url_for('signin'))
    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()
    select_query = """
    SELECT P.Id, P.Name, P.Description, P.Price, P.Image, P.Category
    FROM CartProduct CP
    JOIN Product P ON CP.ProductId = P.Id
    JOIN Cart C ON CP.CartId = C.Id
    JOIN User U ON C.UserId = U.Id
    WHERE U.Email = %s
    """
    curs.execute(select_query, (session['email'],))
    cart_products = curs.fetchall()
    total_query = """
    SELECT SUM(P.Price)
    FROM CartProduct CP
    JOIN Product P ON CP.ProductId = P.Id
    JOIN Cart C ON CP.CartId = C.Id
    JOIN User U ON C.UserId = U.Id
    WHERE U.Email = %s
    """
    curs.execute(total_query, (session['email'],))
    total_price = curs.fetchone()[0]
    select_shipping_query = """
    SELECT * FROM Shipping
    INNER JOIN User ON Shipping.UserId = User.Id
    WHERE User.Email = %s
    """
    curs.execute(select_shipping_query, (session['email'],))
    shipping_info = curs.fetchall()
    curs.close()
    conn.close()
    return render_template('checkout.html', cart_products=cart_products, total_price=total_price, shipping_info=shipping_info)


@app.route('/place_order', methods=['POST'])
def place_order():
    if 'email' not in session:
        return redirect(url_for('signin'))

    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()

    try:
        select_user_id_query = "SELECT Id FROM User WHERE Email = %s"
        curs.execute(select_user_id_query, (session['email'],))
        user_id = curs.fetchone()[0]

        select_cart_query = "SELECT Id FROM Cart WHERE UserId = %s"
        curs.execute(select_cart_query, (user_id,))
        cart_id = curs.fetchone()[0]

        total_query = """
        SELECT SUM(P.Price)
        FROM CartProduct CP
        JOIN Product P ON CP.ProductId = P.Id
        JOIN Cart C ON CP.CartId = C.Id
        JOIN User U ON C.UserId = U.Id
        WHERE U.Id = %s
        """
        curs.execute(total_query, (user_id,))
        total_price = curs.fetchone()[0]

        if total_price is not None:
            total_price = float(total_price)

        insert_order_query = "INSERT INTO `Order` (UserId, Status, Total) VALUES (%s, %s, %s)"
        curs.execute(insert_order_query, (user_id, 'processing', total_price))
        conn.commit()
        order_id = curs.lastrowid

        select_cart_products_query = "SELECT ProductId FROM CartProduct WHERE CartId = %s"
        curs.execute(select_cart_products_query, (cart_id,))
        cart_products = curs.fetchall()

        insert_order_product_query = "INSERT INTO OrderProduct (OrderId, ProductId) VALUES (%s, %s)"
        order_product_data = [(order_id, product_id) for product_id, in cart_products]
        curs.executemany(insert_order_product_query, order_product_data)
        conn.commit()

        delete_cart_products_query = "DELETE FROM CartProduct WHERE CartId = %s"
        curs.execute(delete_cart_products_query, (cart_id,))

        conn.commit()

        return redirect(url_for('order_confirmation', order_id=order_id))

    finally:
        curs.close()
        conn.close()


@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    if 'email' not in session:
        return redirect(url_for('signin'))

    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()

    select_order_query = """
    SELECT O.Id, P.Name, P.Description, P.Price, P.Image, P.Category
    FROM `Order` O
    JOIN OrderProduct OP ON O.Id = OP.OrderId
    JOIN Product P ON OP.ProductId = P.Id
    JOIN User U ON O.UserId = U.Id
    WHERE U.Email = %s AND O.Id = %s
    """
    curs.execute(select_order_query, (session['email'], order_id))
    order_products = curs.fetchall()

    total_query = """
    SELECT SUM(P.Price)
    FROM `Order` O
    JOIN OrderProduct OP ON O.Id = OP.OrderId
    JOIN Product P ON OP.ProductId = P.Id
    JOIN User U ON O.UserId = U.Id
    WHERE U.Email = %s AND O.Id = %s
    """
    curs.execute(total_query, (session['email'], order_id))
    total_price = curs.fetchone()[0]

    select_shipping_query = """
    SELECT * FROM Shipping
    INNER JOIN User ON Shipping.UserId = User.Id
    WHERE User.Email = %s
    """
    curs.execute(select_shipping_query, (session['email'],))
    shipping_info = curs.fetchall()

    curs.close()
    conn.close()

    cart_count = get_cart_count()

    return render_template('order_confirmation.html',
                           order_id=order_id,
                           order_products=order_products,
                           total_price=total_price,
                           shipping_info=shipping_info,
                           cart_count=cart_count)


@app.route('/shipping', methods=['GET', 'POST'])
def shipping():
    if 'email' not in session:
        return redirect(url_for('signin'))

    if request.method == 'POST':
        if 'delete_shipping' in request.form:
            shipping_id = request.form.get('delete_shipping')
            conn = mysql.connector.connect(**db_config)
            curs = conn.cursor()

            delete_shipping_query = "DELETE FROM Shipping WHERE Id = %s"
            curs.execute(delete_shipping_query, (shipping_id,))
            conn.commit()

            curs.close()
            conn.close()

            return redirect(url_for('shipping'))

        else:
            full_name = request.form.get('full_name')
            street_address = request.form.get('street_address')
            city = request.form.get('city')
            state_province = request.form.get('state_province')
            postal_code = request.form.get('postal_code')
            country = request.form.get('country')

            conn = mysql.connector.connect(**db_config)
            curs = conn.cursor()

            select_user_query = "SELECT Id FROM User WHERE Email = %s"
            curs.execute(select_user_query, (session['email'],))
            user_id = curs.fetchone()[0]

            insert_shipping_query = """
            INSERT INTO Shipping (UserId, Full_Name, Street_Address, City, State_Province, Postal_Code, Country)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            shipping_data = (user_id, full_name, street_address, city, state_province, postal_code, country)
            curs.execute(insert_shipping_query, shipping_data)
            conn.commit()

            select_shipping_query = """
            SELECT * FROM Shipping
            INNER JOIN User ON Shipping.UserId = User.Id
            WHERE User.Email = %s
            """
            curs.execute(select_shipping_query, (session['email'],))
            shipping_info = curs.fetchall()

            curs.close()
            conn.close()

            return render_template('shipping.html', shipping_info=shipping_info)

    conn = mysql.connector.connect(**db_config)
    curs = conn.cursor()

    select_shipping_query = """
    SELECT * FROM Shipping
    INNER JOIN User ON Shipping.UserId = User.Id
    WHERE User.Email = %s
    """
    curs.execute(select_shipping_query, (session['email'],))
    shipping_info = curs.fetchall()

    curs.close()
    conn.close()

    return render_template('shipping.html', shipping_info=shipping_info)


@app.route('/videos')
def videos():
    api_key = 'AIzaSyBHQ_sAOG7Nndu5soo5lAp6KDDRZIv4EBg'
    search_query = 'Kazakh meals'
    url = f'https://www.googleapis.com/youtube/v3/search?key={api_key}&part=snippet&type=video&q={search_query}'
    response = requests.get(url)
    data = response.json()

    videos = []
    for item in data['items']:
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        video_thumbnail = item['snippet']['thumbnails']['medium']['url']
        videos.append({'id': video_id, 'title': video_title, 'thumbnail': video_thumbnail})

    videos = videos[:10]
    cart_count = get_cart_count()

    return render_template('videos.html', videos=videos, cart_count=cart_count)



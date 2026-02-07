from flask import Flask, request, redirect, url_for, session, flash, render_template,g
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message, Mail
import json
import os
from psycopg2.extras import RealDictCursor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
mail = Mail(app)

def get_db_connection():
   if "conn" not in g:
      g.conn = psycopg2.connect(os.getenv("DATABASE_URL"))
   return g
   
   with app.app_context():
      db = SQLAlchemy(app)
      db.create_all()
      app.secret_key ="superSecretKey"
      cart_file = 'cart.json'
   if not os.path.exists(cart_file):
      os.makedirs(cart_file, exist_ok = True)
DATABASE_URL = "postgresql://pascaldacky_user:xgk70dACXBBiCiam2VoPG22gL7Qznt1d@dpg-d5veo9sr85hc73e651f0-a/pascaldacky"
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = "True"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "pchahama1103@gmail.com"
app.config["MAIL_PASSWORD"] = "rxdghylubawyhpvq"
app.config["MAIL_DEFAULT_SENDER"] = "pchahama1103@gmail.com"
app.config['DATABASE_URI'] = os.environ.get("DATABASE_URL") 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
if DATABASE_URL:
  app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
   app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:pascaldacky@localhost:5432:/pascals_db"

@app.route('/')
def index():
   return render_template('index.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
   if request.method == 'POST':
      username = request.form.get('username')
      email = request.form.get('email')
      password = request.form.get('password')

      if not username or not email or not password:
         flash("🎗️ please fill out te credentials", "warning")
         return redirect(url_for('register'))


      password_hash = generate_password_hash(password)
      try:
         g.conn = get_db_connection()
         db = SQLAlchemy(app)
         cursor = conn.cursor()
         db.session.add(username)
         db.session.add(email)
         db.session.add(password)
         db.session.commit()
         cursor.execute(" INSERT INTO users (username, email, password) VALUES (%s,%s,%s);", (username, email, password_hash))
         conn.commit()
         conn.close()
         cursor.close()
         flash('Registration successfully!', 'success')
         return redirect(url_for('login'))
      except psycopg2.IntegrityError:
         g.conn.rollback()
         db.session.rollback()
         flash('An Account Arleady Exists try Another', 'warning')
         return redirect(url_for('register'))
      except Exception as e:
         db.session.rollback()
         g.conn.rollback()
         return f"Error: {str(e)}"
         flash(f'Error: {e}', 'danger')
         return redirect(url_for('register')) 
   return render_template('register.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
   if request.method == 'POST':
      username = request.form.get('username')
      password = request.form.get('password')
      if not username or not password:
         flash("username or password not found", "danger")
         return redirect(url_for('register'))

      g.conn = get_db_connection()
      db = SQLAlchemy(app)
      cursor = g.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
      cursor.execute(" SELECT id, username, email, password  FROM  users  WHERE username = %s", (username,))
      user = cursor.fetchone()
      db.session.add(user)
      conn.close()
      conn.close()
      if user and check_password_hash(user["password"], password):
         session['user_id'] = user["id"]
         session['username'] = user["username"]
         session['email'] = user['email']
         flash("you are truly belonging from this sessions", "success")
         return redirect(url_for('products'))
      else:
         flash('username or password may be Invalid!', 'danger')
   return render_template("login.html")



@app.route('/products')
def products():
      conn = get_db_connection()
      cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
      try:
         cursor.execute("SELECT * FROM products")
         products = cursor.fetchall()
         conn.close()
         cursor.close()
      except Exception as e:
         return f" db Error: {e}", "warning"

      return render_template('products.html', products = products)
@app.route('/add_to_cart/<int:pid>', methods = ['GET','POST'])
def add_to_cart(pid):
         user_id = session.get('user_id', 1)
         conn = get_db_connection()
         cursor = conn.cursor()
         cursor.execute(" SELECT * FROM carts WHERE user_id=%s AND product_id=%s",(user_id, pid))
         exist = cursor.fetchone()
         if exist:
            cursor.execute("UPDATE carts SET quantity = quantity + 1 WHERE user_id=%s AND product_id=%s",(user_id, pid))
         else:
            cursor.execute("INSERT INTO carts(user_id, product_id, quantity) VALUES(%s,%s,%s)", (user_id, pid, 1))
         conn.commit()
         cursor.close()
         flash("product added to carts", "success")
         return redirect(url_for('view_cart'))
@app.route('/carts/increase/<int:pid>', methods = ['GET', 'POST'])
def increase_cart(pid):
   user_id = session.get('user_id',1)
   if request.method == 'POST':
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(" UPDATE carts SET quantity = quantity + 1 WHERE user_id=%s AND product_id=%s",(user_id,pid))
      conn.commit()
      cursor.close()
      flash("the cart has been increased", "info")
   return redirect(url_for('view_cart'))

@app.route('/decrease/<int:pdd>', methods = ['GET', 'POST'])
def decrease_cart(pdd):
   user_id = session.get('user_id', 1)
   if request.method == 'POST':
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute("UPDATE carts SET quantity = GREATEST(quantity - 1, 1) WHERE user_id=%s AND product_id=%s",(user_id, pdd))
      conn.commit()
      cursor.close()
      flash("the cart has been decreased", "danger")

   return redirect(url_for('view_cart'))
@app.route('/edit/<int:ped>', methods = ['GET','POST'])
def edit_cart(ped):
   user_id = session.get('user_id', 1)
   if request.method == 'POST':
      new_quantity = int(request.form.get('quantity', ''))
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(" UPDATE carts SET quantity = %s WHERE user_id=%s AND product_id=%s",(new_quantity,user_id,ped))
      conn.commit()
      cursor.close()
      flash("the quantity edited properly", "success")
   return redirect(url_for('view_cart'))
@app.route('/delete_cart/<int:cart_id>', methods = ['GET','POST'])
def delete_cart(cart_id):
   if request.method == 'POST':
      user_id = session.get('user_id', 1)
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute("DELETE FROM carts WHERE user_id=%s AND product_id=%s", (user_id, cart_id,))
      conn.commit()
      cursor.close()
      flash("the cart has been deleted", "danger")
   return redirect(url_for('view_cart'))

@app.route('/view_cart')
def view_cart():
      user_id = session.get('user_id', 1)
      conn = get_db_connection()
      cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
      cursor.execute(""" SELECT  p.id, p.name, p.price, p.image_url, c.quantity FROM carts c JOIN products p  ON c.product_id = p.id WHERE c.user_id = %s""",(user_id,))
      items = cursor.fetchall()
      cursor.close()
      total = sum(item['price'] * item['quantity'] for item in items)
      return render_template('view_cart.html', items = items, total = total)

@app.route('/checkout', methods = ['GET','POST'])
def checkout():
   if request.method == 'POST':
      user_id = session.get('user_id',1)
      username = session.get('username')
      email = session.get('email')
      conn = get_db_connection()
      cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
      cursor.execute(" SELECT p.name, p.price, p.image_url, c.quantity FROM carts c JOIN products p ON c.product_id = p.id WHERE c.user_id=%s",(user_id,))
      items = cursor.fetchall()

      if not items:
         flash("your cart is absolutelly empty", "danger")
         return redirect(url_for('view_cart'))

      total = sum(item['price'] * item['quantity'] for item in items)

      html_content = render_template('email_content.html', items = items, total = total)

      msg = Message( subject= f"🚎🚎🚎 Greatings {email}, we are the moffassatravellers From Tanzania.Book now getting into touch travelling with us via our contacts bellow! 🚎🚎🚎", recipients = [email])

      msg.html = html_content

      mail.send(msg)

      flash(" your order has been placed and sent to your email!","success")
      cursor.execute("DELETE FROM carts WHERE user_id =%s",(user_id,))
      conn.commit()
      cursor.close()

   return redirect(url_for('view_cart'))


@app.errorhandler(404)
def error_handler(error):
   return render_template('404.html', error=error), 404

@app.route('/logout')
def logout():
   if not 'user_id' in session:
      flash("you are not logged in yet!", "info")
      return redirect(url_for('login'))

   session.clear()
   flash('logout success', 'success')
   return redirect('/')


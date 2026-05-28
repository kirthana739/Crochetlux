from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, os, hashlib, json, smtplib, random, string
from functools import wraps
from werkzeug.utils import secure_filename
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'crochetlux_secret_key_2026'

UPLOAD_FOLDER = os.path.join('static', 'images')
REELS_FOLDER  = os.path.join('static', 'reels')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO      = {'mp4', 'mov', 'webm', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ── Gmail config ──────────────────────────────────────────────────
GMAIL_USER     = "crochetlux8@gmail.com"
GMAIL_APP_PASS = ""   # ← paste your 16-char app password
SHOP_NAME      = "CrochetLux"
SHOP_URL       = "https://yourdomain.com"

# ═════════════════════════════════════════════════════════════════
#  EMAIL HELPERS
# ═════════════════════════════════════════════════════════════════
def _send(to_email, subject, html):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f"{SHOP_NAME} <{GMAIL_USER}>"
    msg['To']      = to_email
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.sendmail(GMAIL_USER, to_email, msg.as_string())
        print(f"[MAIL] ✅ {subject} → {to_email}")
    except Exception as e:
        print(f"[MAIL] ❌ {e}")

def _base(content):
    return f"""
<div style="font-family:Arial,sans-serif;max-width:580px;margin:0 auto;background:#fff;
            border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08)">
  <div style="background:linear-gradient(135deg,#e91e8c,#f06292);padding:28px;text-align:center">
    <h1 style="color:#fff;margin:0;font-size:1.5rem">🧶 {SHOP_NAME}</h1>
  </div>
  <div style="padding:32px">{content}</div>
  <div style="background:#fce4ec;padding:16px;text-align:center;font-size:.75rem;color:#999">
    © {SHOP_NAME} · <a href="{SHOP_URL}/shop" style="color:#e91e8c">Shop</a> ·
    <a href="{SHOP_URL}/orders" style="color:#e91e8c">My Orders</a>
  </div>
</div>"""

def email_welcome(to_email, name):
    html = _base(f"""
      <p style="font-size:1.1rem;color:#333">Hi <strong>{name}</strong> 👋</p>
      <p style="color:#555;line-height:1.8">Welcome to <strong>{SHOP_NAME}</strong>!
        Your account has been created. Browse our handcrafted crochet collection. 💖</p>
      <div style="text-align:center;margin:24px 0">
        <a href="{SHOP_URL}/shop" style="background:#e91e8c;color:#fff;padding:12px 32px;
           border-radius:50px;text-decoration:none;font-weight:600">Start Shopping →</a>
      </div>""")
    _send(to_email, f"Welcome to {SHOP_NAME}! 🎀", html)

def email_order_confirmed(to_email, name, order_id, items, total):
    rows = "".join(
        f"<tr><td style='padding:8px 4px;border-bottom:1px solid #f8d7e8'>{i['name']}</td>"
        f"<td style='padding:8px 4px;text-align:center;border-bottom:1px solid #f8d7e8'>{i['qty']}</td>"
        f"<td style='padding:8px 4px;text-align:right;border-bottom:1px solid #f8d7e8'>₹{i['price']*i['qty']:.0f}</td></tr>"
        for i in items)
    html = _base(f"""
      <p style="font-size:1.05rem;color:#333">Hi <strong>{name}</strong> 👋</p>
      <p style="color:#555;line-height:1.7">Order <strong>#{order_id}</strong> confirmed! 💕</p>
      <table style="width:100%;border-collapse:collapse;font-size:.88rem">
        <thead><tr style="background:#fce4ec">
          <th style="padding:8px 4px;text-align:left;color:#c2185b">Item</th>
          <th style="padding:8px 4px;text-align:center;color:#c2185b">Qty</th>
          <th style="padding:8px 4px;text-align:right;color:#c2185b">Price</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        <tfoot><tr style="background:#fce4ec">
          <td colspan="2" style="padding:10px 4px;font-weight:700">Total Paid</td>
          <td style="padding:10px 4px;font-weight:700;color:#e91e8c;text-align:right">₹{total:.0f}</td>
        </tr></tfoot>
      </table>
      <div style="text-align:center;margin:24px 0">
        <a href="{SHOP_URL}/order/{order_id}" style="background:#e91e8c;color:#fff;
           padding:12px 28px;border-radius:50px;text-decoration:none;font-weight:600">
           View Order →</a>
      </div>""")
    _send(to_email, f"✅ Order #{order_id} Confirmed – {SHOP_NAME}", html)

def email_order_shipped(to_email, name, order_id, tracking=None):
    track_html = f"<p style='color:#555'>Tracking: <strong>{tracking}</strong></p>" if tracking else ""
    html = _base(f"""
      <p style="font-size:1.05rem;color:#333">Hi <strong>{name}</strong> 🚚</p>
      <p style="color:#555;line-height:1.7">Order <strong>#{order_id}</strong> has been shipped!</p>
      {track_html}
      <div style="text-align:center;margin:24px 0">
        <a href="{SHOP_URL}/order/{order_id}" style="background:#e91e8c;color:#fff;
           padding:12px 28px;border-radius:50px;text-decoration:none;font-weight:600">
           Track Order →</a>
      </div>""")
    _send(to_email, f"📦 Order #{order_id} Shipped – {SHOP_NAME}", html)

def email_order_delivered(to_email, name, order_id):
    html = _base(f"""
      <p style="font-size:1.05rem;color:#333">Hi <strong>{name}</strong> 🎉</p>
      <p style="color:#555;line-height:1.7">Order <strong>#{order_id}</strong> delivered!
        We hope you love your new crochet pieces. 💖</p>
      <div style="text-align:center;margin:24px 0">
        <a href="{SHOP_URL}/order/{order_id}" style="background:#e91e8c;color:#fff;
           padding:12px 28px;border-radius:50px;text-decoration:none;font-weight:600">
           Leave a Review →</a>
      </div>""")
    _send(to_email, f"🎀 Order #{order_id} Delivered – {SHOP_NAME}", html)

def email_stamp_reward(to_email, name, coupon_code, expiry):
    html = _base(f"""
      <p style="font-size:1.05rem;color:#333">Hi <strong>{name}</strong> 🎉</p>
      <p style="color:#555;line-height:1.7">
        You've completed your stamp card and earned a <strong>₹500 reward!</strong>
      </p>
      <div style="background:linear-gradient(135deg,#e91e8c,#f06292);border-radius:16px;
                  padding:24px;text-align:center;color:#fff;margin:16px 0">
        <div style="font-size:1.8rem;font-weight:700">₹500 OFF</div>
        <div style="font-size:1.3rem;font-weight:700;letter-spacing:3px;
                    background:rgba(255,255,255,.2);border-radius:8px;
                    padding:8px 16px;margin:10px auto;display:inline-block">
          {coupon_code}
        </div>
        <div style="font-size:.8rem;opacity:.9">Valid until {expiry}</div>
      </div>
      <p style="color:#555;font-size:.85rem;text-align:center">
        Use this code at checkout to get ₹500 off your next order!
      </p>""")
    _send(to_email, f"🎀 You earned ₹500 off! – {SHOP_NAME}", html)

# ═════════════════════════════════════════════════════════════════
#  DB HELPERS
# ═════════════════════════════════════════════════════════════════
def get_db():
    db = sqlite3.connect('crochet.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT, phone TEXT, line1 TEXT, line2 TEXT,
            city TEXT, state TEXT, pincode TEXT,
            is_default INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            original_price REAL,
            category TEXT,
            stock INTEGER DEFAULT 0,
            image TEXT,
            is_featured INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            address_id INTEGER,
            total REAL,
            payment_method TEXT,
            payment_status TEXT DEFAULT "pending",
            order_status TEXT DEFAULT "placed",
            txn_id TEXT,
            tracking_number TEXT,
            coupon_code TEXT,
            discount REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS reels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            title TEXT,
            caption TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS stamp_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            total_stamps INTEGER DEFAULT 0,
            coupon_code TEXT,
            coupon_used INTEGER DEFAULT 0,
            coupon_expiry TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS stamp_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_id INTEGER,
            type TEXT DEFAULT "stamp",
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    pw = hashlib.sha256('admin123'.encode()).hexdigest()
    try:
        db.execute("INSERT INTO users(name,email,password,is_admin) VALUES(?,?,?,1)",
                   ('Admin', 'admin@crochetlux.com', pw))
    except: pass
    sample = [
        ('Rosette Dream Bag','Handcrafted hot-pink rosette tote.',1299,1799,'Bags',15,'',1),
        ('Boho Sunset Cardigan','Cream & pink open-knit cardigan.',2499,3200,'Clothing',8,'',1),
        ('Mini Amigurumi Bunny','Adorable stuffed crochet bunny.',699,999,'Toys',25,'',1),
        ('Lace Table Runner','Delicate cream lace runner.',899,1200,'Home',12,'',0),
        ('Flower Crown Headband','Pink floral crochet headband.',449,650,'Accessories',30,'',1),
        ('Shell Stitch Clutch','Evening clutch in blush tones.',1099,1499,'Bags',10,'',0),
        ('Granny Square Throw','Cozy multicolor throw blanket.',3499,4500,'Home',5,'',1),
        ('Cat Ear Beanie','Cute winter beanie with cat ears.',599,850,'Accessories',20,'',0),
    ]
    for p in sample:
        try:
            db.execute("INSERT INTO products(name,description,price,original_price,category,stock,image,is_featured) VALUES(?,?,?,?,?,?,?,?)", p)
        except: pass
    db.commit()
    db.close()

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def get_cart_count():
    if not session.get('user_id'): return 0
    db = get_db()
    c  = db.execute("SELECT SUM(quantity) FROM cart WHERE user_id=?",
                    (session['user_id'],)).fetchone()[0]
    db.close()
    return c or 0

def allowed_file(f):   return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS
def allowed_video(f):  return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED_VIDEO

def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return dec

def admin_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if not session.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*a, **kw)
    return dec

# ═════════════════════════════════════════════════════════════════
#  STAMP CARD HELPERS
# ═════════════════════════════════════════════════════════════════
def generate_coupon():
    return 'CROCHET' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def award_stamp(user_id, order_id, db):
    card = db.execute("SELECT * FROM stamp_cards WHERE user_id=?", (user_id,)).fetchone()
    if not card:
        db.execute("INSERT INTO stamp_cards(user_id,total_stamps) VALUES(?,0)", (user_id,))
        db.commit()
        card = db.execute("SELECT * FROM stamp_cards WHERE user_id=?", (user_id,)).fetchone()
    new_total     = card['total_stamps'] + 1
    coupon_code   = card['coupon_code']
    coupon_expiry = card['coupon_expiry']
    coupon_used   = card['coupon_used']
    reward_unlocked = False
    if new_total % 8 == 0:
        coupon_code     = generate_coupon()
        coupon_expiry   = (datetime.now() + timedelta(days=30)).strftime('%d %b %Y')
        coupon_used     = 0
        reward_unlocked = True
    db.execute("""UPDATE stamp_cards SET total_stamps=?,coupon_code=?,
                  coupon_expiry=?,coupon_used=? WHERE user_id=?""",
               (new_total, coupon_code, coupon_expiry, coupon_used, user_id))
    db.execute("INSERT INTO stamp_history(user_id,order_id,type,description) VALUES(?,?,?,?)",
               (user_id, order_id, 'stamp', f'Order #{order_id} completed'))
    db.commit()
    return reward_unlocked, coupon_code, coupon_expiry

def use_coupon(user_id, code, db):
    db.execute("UPDATE stamp_cards SET coupon_used=1 WHERE user_id=? AND coupon_code=?",
               (user_id, code))
    db.execute("INSERT INTO stamp_history(user_id,type,description) VALUES(?,?,?)",
               (user_id, 'redeemed', f'Coupon {code} redeemed — ₹500 off'))
    db.commit()

# ═════════════════════════════════════════════════════════════════
#  AUTH
# ═════════════════════════════════════════════════════════════════
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name  = request.form['name']
        email = request.form['email']
        pw    = hash_pw(request.form['password'])
        phone = request.form.get('phone', '')
        db    = get_db()
        try:
            db.execute("INSERT INTO users(name,email,password,phone) VALUES(?,?,?,?)",
                       (name, email, pw, phone))
            db.commit()
            email_welcome(email, name)
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Email already registered.', 'error')
        finally:
            db.close()
    return render_template('register.html', cart_count=0)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pw    = hash_pw(request.form['password'])
        db    = get_db()
        user  = db.execute("SELECT * FROM users WHERE email=? AND password=?",
                           (email, pw)).fetchone()
        db.close()
        if user:
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['is_admin']  = bool(user['is_admin'])
            if user['is_admin']: return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        flash('Invalid email or password', 'error')
    return render_template('login.html', cart_count=0)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ═════════════════════════════════════════════════════════════════
#  PUBLIC PAGES
# ═════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    db         = get_db()
    featured   = db.execute("SELECT * FROM products WHERE is_featured=1 LIMIT 8").fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products").fetchall()
    # ── Fetch latest 6 reels for the home page preview section ──
    reels      = db.execute("SELECT * FROM reels ORDER BY created_at DESC LIMIT 6").fetchall()
    db.close()
    return render_template('index.html', featured=featured, categories=categories,
                           reels=reels, cart_count=get_cart_count())

@app.route('/shop')
def shop():
    db     = get_db()
    cat    = request.args.get('cat', '')
    search = request.args.get('q', '')
    sort   = request.args.get('sort', 'newest')
    q      = "SELECT * FROM products WHERE 1=1"
    params = []
    if cat:    q += " AND category=?";                          params.append(cat)
    if search: q += " AND (name LIKE ? OR description LIKE ?)"; params += [f'%{search}%'] * 2
    q += {' low': ' ORDER BY price ASC', ' high': ' ORDER BY price DESC'}.get(
         ' ' + sort, ' ORDER BY created_at DESC')
    products   = db.execute(q, params).fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products").fetchall()
    db.close()
    return render_template('shop.html', products=products, categories=categories,
                           current_cat=cat, search=search, sort=sort,
                           cart_count=get_cart_count())

@app.route('/product/<int:pid>')
def product_detail(pid):
    db      = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not product:
        db.close(); flash('Product not found', 'error'); return redirect(url_for('shop'))
    product = dict(product)
    reviews = [dict(r) for r in db.execute(
        "SELECT r.*,u.name as reviewer_name FROM reviews r JOIN users u ON r.user_id=u.id "
        "WHERE r.product_id=? ORDER BY r.created_at DESC", (pid,)).fetchall()]
    avg_rating  = sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0
    in_wishlist = False
    if session.get('user_id'):
        in_wishlist = bool(db.execute(
            "SELECT id FROM wishlist WHERE user_id=? AND product_id=?",
            (session['user_id'], pid)).fetchone())
    db.close()
    return render_template('product.html', product=product, reviews=reviews,
                           avg_rating=avg_rating, in_wishlist=in_wishlist,
                           cart_count=get_cart_count())

# ═════════════════════════════════════════════════════════════════
#  CART
# ═════════════════════════════════════════════════════════════════
@app.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    pid = int(request.form['product_id'])
    qty = int(request.form.get('quantity', 1))
    db  = get_db()
    ex  = db.execute("SELECT * FROM cart WHERE user_id=? AND product_id=?",
                     (session['user_id'], pid)).fetchone()
    if ex: db.execute("UPDATE cart SET quantity=quantity+? WHERE id=?", (qty, ex['id']))
    else:  db.execute("INSERT INTO cart(user_id,product_id,quantity) VALUES(?,?,?)",
                      (session['user_id'], pid, qty))
    db.commit(); db.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': get_cart_count()})
    flash('Added to cart! 🛍️', 'success')
    return redirect(request.referrer or url_for('shop'))

@app.route('/cart')
@login_required
def cart():
    db    = get_db()
    items = db.execute("""SELECT c.id,c.quantity,p.id as product_id,p.name,p.price,p.image
                          FROM cart c JOIN products p ON c.product_id=p.id
                          WHERE c.user_id=?""", (session['user_id'],)).fetchall()
    total = sum(i['price'] * i['quantity'] for i in items)
    db.close()
    return render_template('cart.html', items=items, total=total, cart_count=get_cart_count())

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    cid = int(request.form['cart_id'])
    qty = int(request.form['quantity'])
    db  = get_db()
    if qty <= 0: db.execute("DELETE FROM cart WHERE id=? AND user_id=?", (cid, session['user_id']))
    else:        db.execute("UPDATE cart SET quantity=? WHERE id=? AND user_id=?",
                            (qty, cid, session['user_id']))
    db.commit(); db.close()
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:cid>')
@login_required
def remove_cart(cid):
    db = get_db()
    db.execute("DELETE FROM cart WHERE id=? AND user_id=?", (cid, session['user_id']))
    db.commit(); db.close()
    flash('Item removed', 'success')
    return redirect(url_for('cart'))

# ═════════════════════════════════════════════════════════════════
#  WISHLIST
# ═════════════════════════════════════════════════════════════════
@app.route('/wishlist/toggle', methods=['POST'])
@login_required
def toggle_wishlist():
    pid = int(request.form['product_id'])
    db  = get_db()
    ex  = db.execute("SELECT id FROM wishlist WHERE user_id=? AND product_id=?",
                     (session['user_id'], pid)).fetchone()
    if ex: db.execute("DELETE FROM wishlist WHERE id=?", (ex['id'],)); added = False
    else:  db.execute("INSERT INTO wishlist(user_id,product_id) VALUES(?,?)",
                      (session['user_id'], pid));                       added = True
    db.commit(); db.close()
    return jsonify({'success': True, 'added': added})

@app.route('/wishlist')
@login_required
def wishlist():
    db    = get_db()
    items = db.execute("SELECT p.* FROM wishlist w JOIN products p ON w.product_id=p.id "
                       "WHERE w.user_id=?", (session['user_id'],)).fetchall()
    db.close()
    return render_template('wishlist.html', items=items, cart_count=get_cart_count())

# ═════════════════════════════════════════════════════════════════
#  CHECKOUT & ORDERS
# ═════════════════════════════════════════════════════════════════
@app.route('/checkout')
@login_required
def checkout():
    db    = get_db()
    items = db.execute("""SELECT c.id,c.quantity,p.id as product_id,p.name,p.price,p.image
                          FROM cart c JOIN products p ON c.product_id=p.id
                          WHERE c.user_id=?""", (session['user_id'],)).fetchall()
    if not items:
        flash('Your cart is empty!', 'error'); return redirect(url_for('cart'))
    addresses = db.execute("SELECT * FROM addresses WHERE user_id=?",
                           (session['user_id'],)).fetchall()
    total = sum(i['price'] * i['quantity'] for i in items)
    db.close()
    return render_template('checkout.html', items=items, addresses=addresses,
                           total=total, cart_count=get_cart_count())

@app.route('/address/add', methods=['POST'])
@login_required
def add_address():
    db = get_db()
    db.execute("INSERT INTO addresses(user_id,name,phone,line1,line2,city,state,pincode) VALUES(?,?,?,?,?,?,?,?)",
               (session['user_id'], request.form['name'], request.form['phone'],
                request.form['line1'], request.form.get('line2', ''),
                request.form['city'], request.form['state'], request.form['pincode']))
    db.commit(); db.close()
    flash('Address saved!', 'success')
    return redirect(url_for('checkout'))

@app.route('/order/place', methods=['POST'])
@login_required
def place_order():
    addr_id = request.form.get('address_id') or None
    payment = request.form.get('payment_method', 'cod')
    coupon  = request.form.get('coupon_code', '').strip().upper()
    db      = get_db()
    items   = db.execute("""SELECT c.quantity,p.id,p.name,p.price
                            FROM cart c JOIN products p ON c.product_id=p.id
                            WHERE c.user_id=?""", (session['user_id'],)).fetchall()
    if not items: db.close(); return redirect(url_for('cart'))
    total    = sum(i['price'] * i['quantity'] for i in items)
    shipping = 0 if total >= 999 else 99
    discount = 0
    if coupon:
        card = db.execute(
            "SELECT * FROM stamp_cards WHERE user_id=? AND coupon_code=? AND coupon_used=0",
            (session['user_id'], coupon)).fetchone()
        if card:
            try:
                expiry = datetime.strptime(card['coupon_expiry'], '%d %b %Y')
                if datetime.now() <= expiry: discount = 500
            except: discount = 500
    final_total = max(0, total + shipping - discount)
    pay_status  = 'paid' if payment == 'cod' else 'pending'
    cur = db.execute("""INSERT INTO orders(user_id,address_id,total,payment_method,
                        payment_status,order_status,coupon_code,discount)
                        VALUES(?,?,?,?,?,?,?,?)""",
                     (session['user_id'], addr_id, final_total, payment,
                      pay_status, 'placed', coupon or None, discount))
    oid = cur.lastrowid
    for i in items:
        db.execute("INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)",
                   (oid, i['id'], i['quantity'], i['price']))
        db.execute("UPDATE products SET stock=MAX(0,stock-?) WHERE id=?",
                   (i['quantity'], i['id']))
    db.execute("DELETE FROM cart WHERE user_id=?", (session['user_id'],))
    db.commit()
    if coupon and discount > 0:
        use_coupon(session['user_id'], coupon, db)
    reward_unlocked, new_coupon, expiry = award_stamp(session['user_id'], oid, db)
    if payment == 'cod':
        user = db.execute("SELECT name,email FROM users WHERE id=?",
                          (session['user_id'],)).fetchone()
        items_list = [{'name': i['name'], 'qty': i['quantity'], 'price': i['price']} for i in items]
        email_order_confirmed(user['email'], user['name'], oid, items_list, final_total)
        if reward_unlocked:
            email_stamp_reward(user['email'], user['name'], new_coupon, expiry)
    db.close()
    if reward_unlocked:
        flash(f'🎉 Order #{oid} placed! You earned a ₹500 reward coupon! Check your stamp card!', 'success')
    elif discount > 0:
        flash(f'✅ Order #{oid} placed! ₹500 coupon applied!', 'success')
    else:
        flash(f'✅ Order #{oid} placed! You earned a stamp! 🧶', 'success')
    if payment == 'online': return redirect(url_for('upi_pay_page', oid=oid))
    return redirect(url_for('order_success', oid=oid))

@app.route('/order/success/<int:oid>')
@login_required
def order_success(oid):
    db    = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?",
                       (oid, session['user_id'])).fetchone()
    if not order: db.close(); return redirect(url_for('my_orders'))
    items = db.execute("""SELECT oi.*,p.name,p.image FROM order_items oi
                          JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""",
                       (oid,)).fetchall()
    db.close()
    return render_template('order_success.html', order=order, items=items, cart_count=0)

@app.route('/orders')
@login_required
def my_orders():
    db     = get_db()
    orders = db.execute("""SELECT o.*,COUNT(oi.id) as item_count
                           FROM orders o LEFT JOIN order_items oi ON o.id=oi.order_id
                           WHERE o.user_id=? GROUP BY o.id ORDER BY o.created_at DESC""",
                        (session['user_id'],)).fetchall()
    db.close()
    return render_template('orders.html', orders=orders, cart_count=get_cart_count())

@app.route('/order/<int:oid>')
@login_required
def order_detail(oid):
    db    = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?",
                       (oid, session['user_id'])).fetchone()
    if not order:
        db.close(); flash('Order not found', 'error'); return redirect(url_for('my_orders'))
    items = db.execute("""SELECT oi.*,p.name,p.image FROM order_items oi
                          JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""",
                       (oid,)).fetchall()
    addr = db.execute("SELECT * FROM addresses WHERE id=?",
                      (order['address_id'],)).fetchone() if order['address_id'] else None
    db.close()
    return render_template('order_detail.html', order=order, items=items,
                           addr=addr, cart_count=get_cart_count())

# ═════════════════════════════════════════════════════════════════
#  UPI PAYMENT
# ═════════════════════════════════════════════════════════════════
@app.route('/pay/upi/<int:oid>')
@login_required
def upi_pay_page(oid):
    db    = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?",
                       (oid, session['user_id'])).fetchone()
    db.close()
    if not order: return redirect(url_for('my_orders'))
    upi_id  = 'kirthanaganeshkunder@okhdfcbank'
    total   = order['total']
    upi_url = (f"upi://pay?pa={upi_id}&pn=CrochetLux"
               f"&am={total:.2f}&cu=INR&tn=CrochetLux+Order+{oid}")
    return render_template('upi_payment.html', total=total, order_id=oid,
                           upi_url=upi_url, cart_count=get_cart_count())

@app.route('/order/confirm-payment', methods=['POST'])
@login_required
def confirm_payment():
    data     = request.get_json()
    order_id = data.get('order_id')
    utr      = data.get('utr', '').strip()
    if not order_id or len(utr) < 10:
        return jsonify({'success': False, 'error': 'Invalid data'})
    db    = get_db()
    order = db.execute(
        "SELECT * FROM orders WHERE id=? AND user_id=? AND payment_status='pending'",
        (order_id, session['user_id'])).fetchone()
    if not order:
        db.close(); return jsonify({'success': False, 'error': 'Order not found or already paid'})
    db.execute("UPDATE orders SET payment_status='paid', txn_id=? WHERE id=?", (utr, order_id))
    db.commit()
    items = db.execute("""SELECT oi.quantity as qty,oi.price,p.name
                          FROM order_items oi JOIN products p ON oi.product_id=p.id
                          WHERE oi.order_id=?""", (order_id,)).fetchall()
    user  = db.execute("SELECT name,email FROM users WHERE id=?",
                       (session['user_id'],)).fetchone()
    items_list = [{'name': i['name'], 'qty': i['qty'], 'price': i['price']} for i in items]
    total      = sum(i['price'] * i['qty'] for i in items)
    reward_unlocked, new_coupon, expiry = award_stamp(session['user_id'], order_id, db)
    db.close()
    email_order_confirmed(user['email'], user['name'], order_id, items_list, total)
    if reward_unlocked:
        email_stamp_reward(user['email'], user['name'], new_coupon, expiry)
    return jsonify({'success': True, 'items': items_list, 'total': total})

@app.route('/order/payment-status/<int:oid>')
@login_required
def payment_status(oid):
    db    = get_db()
    order = db.execute("SELECT payment_status FROM orders WHERE id=? AND user_id=?",
                       (oid, session['user_id'])).fetchone()
    if not order: db.close(); return jsonify({'status': 'not_found'})
    if order['payment_status'] == 'paid':
        items = db.execute("""SELECT oi.quantity as qty,oi.price,p.name
                              FROM order_items oi JOIN products p ON oi.product_id=p.id
                              WHERE oi.order_id=?""", (oid,)).fetchall()
        total = sum(i['price'] * i['qty'] for i in items)
        db.close()
        return jsonify({'status': 'paid',
                        'items': [{'name': i['name'], 'qty': i['qty'], 'price': i['price']} for i in items],
                        'total': total})
    st = order['payment_status']; db.close()
    return jsonify({'status': st})

# ═════════════════════════════════════════════════════════════════
#  COUPON
# ═════════════════════════════════════════════════════════════════
@app.route('/coupon/apply', methods=['POST'])
@login_required
def apply_coupon():
    code = request.get_json().get('code', '').strip().upper()
    db   = get_db()
    card = db.execute(
        "SELECT * FROM stamp_cards WHERE user_id=? AND coupon_code=? AND coupon_used=0",
        (session['user_id'], code)).fetchone()
    if not card:
        db.close(); return jsonify({'success': False, 'message': 'Invalid or already used coupon'})
    try:
        expiry = datetime.strptime(card['coupon_expiry'], '%d %b %Y')
        if datetime.now() > expiry:
            db.close(); return jsonify({'success': False, 'message': 'Coupon has expired'})
    except: pass
    db.close()
    return jsonify({'success': True, 'discount': 500, 'message': '₹500 discount applied! 🎉'})

# ═════════════════════════════════════════════════════════════════
#  STAMP CARD
# ═════════════════════════════════════════════════════════════════
@app.route('/stamp-card')
@login_required
def stamp_card():
    db   = get_db()
    card = db.execute("SELECT * FROM stamp_cards WHERE user_id=?",
                      (session['user_id'],)).fetchone()
    if not card:
        db.execute("INSERT INTO stamp_cards(user_id,total_stamps) VALUES(?,0)",
                   (session['user_id'],))
        db.commit()
        card = db.execute("SELECT * FROM stamp_cards WHERE user_id=?",
                          (session['user_id'],)).fetchone()
    history = db.execute(
        "SELECT * FROM stamp_history WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
        (session['user_id'],)).fetchall()
    db.close()
    stamps      = card['total_stamps']
    current     = stamps % 8
    has_reward  = (stamps > 0 and current == 0 and
                   card['coupon_code'] and not card['coupon_used'])
    stamp_data  = {
        'stamps':        stamps,
        'total_stamps':  stamps,
        'current':       current,
        'has_reward':    has_reward,
        'coupon_code':   card['coupon_code']   or '',
        'coupon_expiry': card['coupon_expiry'] or '',
        'pct':           int(current / 8 * 100),
    }
    return render_template('stamp_card.html', stamp_card=stamp_data,
                           history=history, cart_count=get_cart_count())

# ═════════════════════════════════════════════════════════════════
#  REVIEWS
# ═════════════════════════════════════════════════════════════════
@app.route('/review/add', methods=['POST'])
@login_required
def add_review():
    pid     = int(request.form['product_id'])
    rating  = int(request.form['rating'])
    comment = request.form['comment']
    db      = get_db()
    db.execute("INSERT INTO reviews(product_id,user_id,rating,comment) VALUES(?,?,?,?)",
               (pid, session['user_id'], rating, comment))
    db.commit(); db.close()
    flash('Review submitted! Thank you 💖', 'success')
    return redirect(url_for('product_detail', pid=pid))

# ═════════════════════════════════════════════════════════════════
#  ACCOUNT
# ═════════════════════════════════════════════════════════════════
@app.route('/account')
@login_required
def account():
    db   = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    addr = db.execute("SELECT * FROM addresses WHERE user_id=?",
                      (session['user_id'],)).fetchall()
    db.close()
    return render_template('account.html', user=user, addresses=addr,
                           cart_count=get_cart_count())

# ═════════════════════════════════════════════════════════════════
#  REELS
# ═════════════════════════════════════════════════════════════════
@app.route('/reels')
def reels_page():
    db    = get_db()
    reels = db.execute("SELECT * FROM reels ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('reels.html', reels=reels, cart_count=get_cart_count())

@app.route('/admin/reels')
@admin_required
def admin_reels():
    db    = get_db()
    reels = db.execute("SELECT * FROM reels ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('admin/reels.html', reels=reels, cart_count=0)

@app.route('/admin/reels/add', methods=['POST'])
@admin_required
def admin_add_reel():
    f = request.files.get('video')
    if not f or not f.filename:
        flash('Please select a video file', 'error')
        return redirect(url_for('admin_reels'))
    if not allowed_video(f.filename):
        flash('Invalid file. Use MP4, MOV or WEBM', 'error')
        return redirect(url_for('admin_reels'))
    import time
    filename = f"reel_{int(time.time())}.{f.filename.rsplit('.',1)[-1].lower()}"
    os.makedirs(REELS_FOLDER, exist_ok=True)
    f.save(os.path.join(REELS_FOLDER, filename))
    db = get_db()
    db.execute("INSERT INTO reels(filename,title,caption) VALUES(?,?,?)",
               (filename, request.form.get('title','').strip(),
                request.form.get('caption','').strip()))
    db.commit(); db.close()
    flash('Reel uploaded! 🎬', 'success')
    return redirect(url_for('admin_reels'))

@app.route('/admin/reels/delete/<int:rid>', methods=['POST'])
@admin_required
def admin_delete_reel(rid):
    db   = get_db()
    reel = db.execute("SELECT * FROM reels WHERE id=?", (rid,)).fetchone()
    if reel:
        fp = os.path.join(REELS_FOLDER, reel['filename'])
        if os.path.exists(fp): os.remove(fp)
        db.execute("DELETE FROM reels WHERE id=?", (rid,))
        db.commit()
        flash('Reel deleted', 'success')
    db.close()
    return redirect(url_for('admin_reels'))

# ═════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═════════════════════════════════════════════════════════════════
@app.route('/admin')
@admin_required
def admin_dashboard():
    db    = get_db()
    stats = {
        'products': db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        'orders':   db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        'users':    db.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0],
        'revenue':  db.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE payment_status='paid'").fetchone()[0],
        'pending':  db.execute("SELECT COUNT(*) FROM orders WHERE order_status='placed'").fetchone()[0],
    }
    recent_orders = db.execute("""
        SELECT o.*,u.name as uname,u.email as uemail,COUNT(oi.id) as item_count
        FROM orders o JOIN users u ON o.user_id=u.id
        LEFT JOIN order_items oi ON o.id=oi.order_id
        GROUP BY o.id ORDER BY o.created_at DESC LIMIT 15""").fetchall()
    db.close()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_orders=recent_orders, cart_count=0)

@app.route('/admin/products')
@admin_required
def admin_products():
    db       = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('admin/products.html', products=products, cart_count=0)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        image = ''
        f = request.files.get('image')
        if f and f.filename and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image = filename
        db = get_db()
        db.execute("""INSERT INTO products(name,description,price,original_price,
                      category,stock,image,is_featured) VALUES(?,?,?,?,?,?,?,?)""",
                   (request.form['name'], request.form['description'],
                    float(request.form['price']),
                    float(request.form.get('original_price') or 0),
                    request.form['category'], int(request.form['stock']),
                    image, int(request.form.get('is_featured', 0))))
        db.commit(); db.close()
        flash('Product added! ✅', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', product=None, cart_count=0)

@app.route('/admin/product/edit/<int:pid>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(pid):
    db      = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not product:
        db.close(); flash('Not found', 'error'); return redirect(url_for('admin_products'))
    if request.method == 'POST':
        image = product['image']
        f = request.files.get('image')
        if f and f.filename and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image = filename
        db.execute("""UPDATE products SET name=?,description=?,price=?,original_price=?,
                      category=?,stock=?,image=?,is_featured=? WHERE id=?""",
                   (request.form['name'], request.form['description'],
                    float(request.form['price']),
                    float(request.form.get('original_price') or 0),
                    request.form['category'], int(request.form['stock']),
                    image, int(request.form.get('is_featured', 0)), pid))
        db.commit(); db.close()
        flash('Product updated! ✅', 'success')
        return redirect(url_for('admin_products'))
    db.close()
    return render_template('admin/product_form.html', product=dict(product), cart_count=0)

@app.route('/admin/product/delete/<int:pid>', methods=['POST'])
@admin_required
def admin_delete_product(pid):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit(); db.close()
    flash('Product deleted', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    db     = get_db()
    status = request.args.get('status', '')
    q      = """SELECT o.*,u.name as uname,u.email as uemail,COUNT(oi.id) as item_count
                FROM orders o JOIN users u ON o.user_id=u.id
                LEFT JOIN order_items oi ON o.id=oi.order_id"""
    params = []
    if status: q += " WHERE o.order_status=?"; params.append(status)
    q += " GROUP BY o.id ORDER BY o.created_at DESC"
    orders = db.execute(q, params).fetchall()
    db.close()
    return render_template('admin/orders.html', orders=orders,
                           current_status=status, cart_count=0)

@app.route('/admin/order/<int:oid>')
@admin_required
def admin_order_detail(oid):
    db    = get_db()
    order = db.execute("""SELECT o.*,u.name as uname,u.email as uemail
                          FROM orders o JOIN users u ON o.user_id=u.id
                          WHERE o.id=?""", (oid,)).fetchone()
    if not order:
        db.close(); flash('Not found', 'error'); return redirect(url_for('admin_orders'))
    items = db.execute("""SELECT oi.*,p.name,p.image FROM order_items oi
                          JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""",
                       (oid,)).fetchall()
    addr = db.execute("SELECT * FROM addresses WHERE id=?",
                      (order['address_id'],)).fetchone() if order['address_id'] else None
    db.close()
    return render_template('admin/order_detail.html', order=order, items=items,
                           addr=addr, cart_count=0)

@app.route('/admin/order/update/<int:oid>', methods=['POST'])
@admin_required
def admin_update_order(oid):
    new_status = request.form['order_status']
    tracking   = request.form.get('tracking_number', '').strip()
    db         = get_db()
    order      = db.execute("SELECT o.*,u.name as uname,u.email as uemail "
                            "FROM orders o JOIN users u ON o.user_id=u.id WHERE o.id=?",
                            (oid,)).fetchone()
    if not order:
        db.close(); flash('Not found', 'error'); return redirect(url_for('admin_orders'))
    old_status = order['order_status']
    db.execute("UPDATE orders SET order_status=?,tracking_number=? WHERE id=?",
               (new_status, tracking or order['tracking_number'], oid))
    db.commit()
    if new_status != old_status:
        if new_status == 'shipped':
            email_order_shipped(order['uemail'], order['uname'], oid, tracking or None)
        elif new_status == 'delivered':
            email_order_delivered(order['uemail'], order['uname'], oid)
    db.close()
    flash(f'Order #{oid} updated to "{new_status}" ✅', 'success')
    return redirect(url_for('admin_order_detail', oid=oid))

# ═════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(REELS_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
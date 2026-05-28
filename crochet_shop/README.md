# 🧶 CrochetLux — Luxury Crochet E-Commerce Website

A full-featured, luxury e-commerce website for selling handcrafted crochet products.
Built with **Python Flask** + **SQLite3** + **HTML/CSS/JS**.

---

## ✨ Features

- 3D animated 5-slide splash screen (auto-hides after 5 seconds)
- Hot pink & cream luxury theme with full animations
- Product listing with stock count, category filters, search & sort
- Add to Cart / Wishlist / Product detail with star reviews
- Address management (multiple addresses per user)
- Cash on Delivery support
- UPI payment (direct deep-link to GPay, PhonePe, Paytm)
- Order confirmation email via Gmail SMTP
- Admin panel: add/edit/delete products, manage orders, view stats
- Stock auto-decrements on purchase
- Mobile responsive on all screen sizes
- User account creation, login, profile page

---

## 🚀 Setup (VS Code)

### Step 1 — Install Python dependencies
```bash
pip install flask flask-mail werkzeug
```

### Step 2 — Configure Gmail (for order emails)
Open `app.py` and update lines 13–14:
```python
app.config['MAIL_USERNAME'] = 'your_gmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_16_char_app_password'
app.config['MAIL_DEFAULT_SENDER'] = 'your_gmail@gmail.com'
```

**How to get Gmail App Password:**
1. Go to https://myaccount.google.com
2. Security → 2-Step Verification → Turn ON
3. Security → App passwords → Generate for "Mail"
4. Copy the 16-character password into the config above

### Step 3 — Set your UPI ID
In `app.py`, find line with `upi_id` and update:
```python
upi_id = 'yourname@upi'   # e.g. yourname@paytm, yourname@okaxis
```

### Step 4 — Run the website
```bash
python app.py
```
Open your browser: **http://localhost:5000**

---

## 🔐 Admin Panel

URL: http://localhost:5000/admin

| Field    | Value                    |
|----------|--------------------------|
| Email    | admin@crochetlux.com     |
| Password | admin123                 |

**Admin can:**
- Add / Edit / Delete products (with image upload)
- Set product as Featured (shows on homepage)
- View all customer orders
- Update order status (Placed → Processing → Shipped → Delivered)
- View revenue and customer stats

---

## 📁 Project Structure

```
crochet_shop/
├── app.py                    ← Main Flask app (all routes + logic)
├── requirements.txt          ← Python packages
├── crochet.db                ← SQLite database (auto-created on first run)
├── static/
│   └── images/               ← Product images go here
│       └── placeholder.svg
└── templates/
    ├── base.html             ← Navbar, footer, shared styles
    ├── index.html            ← Homepage with splash screen
    ├── shop.html             ← Product listing page
    ├── product.html          ← Product detail + reviews
    ├── cart.html             ← Shopping cart
    ├── checkout.html         ← Checkout with address + payment
    ├── order_success.html    ← Order confirmation page
    ├── orders.html           ← My orders list
    ├── order_detail.html     ← Single order detail
    ├── login.html            ← Login page
    ├── register.html         ← Register page
    ├── account.html          ← User profile
    ├── wishlist.html         ← Wishlist page
    ├── upi_payment.html      ← UPI payment deep-links
    └── admin/
        ├── base_admin.html   ← Admin layout + sidebar
        ├── dashboard.html    ← Stats + recent orders
        ├── products.html     ← Products list
        ├── add_product.html  ← Add new product form
        ├── edit_product.html ← Edit product form
        └── orders.html       ← All orders management
```

---

## 🖼️ Adding Product Images

1. Put your crochet product photos in `static/images/`
2. Name them exactly as set in admin (e.g. `bag1.jpg`, `bunny1.jpg`)
3. Or upload via admin panel — images are auto-saved to `static/images/`

---

## 💳 Payment Methods

| Method | How it works |
|--------|-------------|
| Cash on Delivery | Order placed, paid on delivery |
| UPI / Online | Deep-links open GPay / PhonePe / Paytm directly on phone |

No Razorpay API key needed — UPI works via standard deep-links on mobile!

---

## 📧 Email Notifications

When an order is placed, a beautiful HTML email is automatically sent to the buyer with:
- Order ID and date
- Itemized product list
- Total amount
- Payment method

Order status update emails are also sent when admin changes order status.

---

## 🛠️ Default Sample Products (auto-seeded)

The database is pre-loaded with 8 sample products so you can see the shop immediately:
- Rosette Dream Bag
- Boho Sunset Cardigan
- Mini Amigurumi Bunny
- Lace Table Runner
- Flower Crown Headband
- Shell Stitch Clutch
- Granny Square Throw
- Cat Ear Beanie

Replace these via the Admin panel with your real crochet products!

---

## ❓ Common Issues

**Q: Email not sending?**
A: Make sure 2-Step Verification is ON in Gmail and you're using an App Password (not your regular Gmail password).

**Q: Images not showing?**
A: Place your `.jpg`/`.png` files in `static/images/` with the same filename as entered in admin.

**Q: Database errors?**
A: Delete `crochet.db` and restart — it will be auto-recreated fresh.

---

Made with ❤️ for CrochetLux

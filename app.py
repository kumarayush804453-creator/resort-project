from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import pandas as pd
import io

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'a_very_secret_key_for_flash_messages'

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kumarayush804453@gmail.com'
app.config['MAIL_PASSWORD'] = 'ifyj jjmk owev douy'
ADMIN_EMAIL = 'kumarayush804453@gmail.com'

mail = Mail(app)

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

db = SQLAlchemy(app)

# Database Table Setup
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    check_in = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(500))
    status = db.Column(db.String(20), default='Pending')

with app.app_context():
    db.create_all()
    # Auto-add missing phone column if database already existed on server
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text('ALTER TABLE booking ADD COLUMN phone VARCHAR(20)'))
            conn.commit()
    except Exception:
        pass

# --- PUBLIC ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        room_type = request.form['room_type']
        check_in = request.form['check_in']
        message = request.form.get('message', '')

        if not name or not email or not phone or not check_in:
            flash("Please fill in all required fields (Name, Email, Phone, Check-in Date).", "danger")
            return redirect(url_for('home'))

        try:
            new_booking = Booking(
                name=name, 
                email=email, 
                phone=phone, 
                room_type=room_type, 
                check_in=check_in, 
                message=message
            )
            db.session.add(new_booking)
            db.session.commit()

            # --- EMAIL TO CLIENT & ADMIN ON BOOKING REQUEST ---
            try:
                # 1. Customer Email
                cust_msg = Message(
                    subject="Booking Received - Paradise Luxury Resort",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[email]
                )
                cust_msg.body = f"Hello {name},\n\nThank you for choosing Paradise Resort!\nYour booking request for {room_type} on {check_in} has been successfully received.\n\nCurrent Status: Pending\n\nWe will update you once your booking is confirmed.\n\nBest Regards,\nParadise Resort Team"
                mail.send(cust_msg)

                # 2. Admin Alert Email
                admin_msg = Message(
                    subject=f"New Booking Alert: {name}",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[ADMIN_EMAIL]
                )
                admin_msg.body = f"New Booking Received!\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nRoom: {room_type}\nCheck-in: {check_in}\nMessage: {message}"
                mail.send(admin_msg)
            except Exception as mail_err:
                print("Mail Error:", mail_err)

            flash(f"Thank you, {name}! Your {room_type} booking request is received.", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Database Error: {str(e)}", "danger")
            return redirect(url_for('home'))

    return render_template('index.html')


# --- ADMIN ROUTES ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials!", "danger")
            
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    query = Booking.query

    if search_query:
        query = query.filter(
            (Booking.name.contains(search_query)) | 
            (Booking.phone.contains(search_query)) | 
            (Booking.email.contains(search_query))
        )
    if status_filter:
        query = query.filter(Booking.status == status_filter)

    bookings = query.order_by(Booking.id.desc()).all()
    return render_template('admin.html', bookings=bookings, search_query=search_query, status_filter=status_filter)

@app.route('/admin/export')
def export_excel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    bookings = Booking.query.all()
    data = []
    for b in bookings:
        data.append({
            'Booking ID': b.id,
            'Full Name': b.name,
            'Email': b.email,
            'Phone': b.phone,
            'Room Type': b.room_type,
            'Check-in Date': b.check_in,
            'Special Request': b.message,
            'Status': b.status
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Bookings')
    
    output.seek(0)
    return send_file(output, download_name='Resort_Bookings.xlsx', as_attachment=True)

# --- STATUS UPDATE WITH EMAIL NOTIFICATION TO CLIENT ---
@app.route('/admin/status/<int:id>/<string:new_status>')
def update_status(id, new_status):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    booking = Booking.query.get_or_404(id)
    booking.status = new_status
    db.session.commit()

    # --- EMAIL TO CLIENT ON STATUS CHANGE ---
    try:
        status_msg = Message(
            subject=f"Booking Update: Status is now {new_status} - Paradise Resort",
            sender=app.config['MAIL_USERNAME'],
            recipients=[booking.email]
        )
        
        if new_status == 'Confirmed':
            status_msg.body = f"Hello {booking.name},\n\nGreat news! Your booking for {booking.room_type} on {booking.check_in} has been CONFIRMED!\n\nWe look forward to welcoming you at Paradise Resort.\n\nWarm regards,\nParadise Resort Management"
        elif new_status == 'Cancelled':
            status_msg.body = f"Hello {booking.name},\n\nWe regret to inform you that your booking for {booking.room_type} on {booking.check_in} has been CANCELLED.\n\nIf you have any questions, please contact our support team.\n\nBest regards,\nParadise Resort Management"
        else:
            status_msg.body = f"Hello {booking.name},\n\nYour booking status for {booking.room_type} on {booking.check_in} has been updated to: {new_status}.\n\nBest regards,\nParadise Resort Management"

        mail.send(status_msg)
    except Exception as mail_err:
        print("Status Email Error:", mail_err)

    flash(f"Booking #{id} status updated to {new_status} and notification email sent to customer.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:id>')
def delete_booking(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    booking = Booking.query.get_or_404(id)
    db.session.delete(booking)
    db.session.commit()
    flash(f"Booking #{id} deleted successfully.", "warning")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)

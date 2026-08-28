from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
# Image ko properly fetch karne ke liye setup
app.config['STATIC_FOLDER'] = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'a_very_secret_key_for_flash_messages'

db = SQLAlchemy(app)

# Database Table Setup
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    check_in = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(500))

with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
@app.route('/admin')
def admin():
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template('admin.html', bookings=bookings)
def home():
    if request.method == 'POST':
        # Form submission logic
        name = request.form['name']
        email = request.form['email']
        room_type = request.form['room_type']
        check_in = request.form['check_in']
        message = request.form.get('message', '')

        # Basic Validation
        if not name or not email or not check_in:
            flash("Please fill in all required fields (Name, Email, Check-in Date).", "danger")
            return redirect(url_for('home'))

        try:
            # Database saving
            new_booking = Booking(name=name, email=email, room_type=room_type, check_in=check_in, message=message)
            db.session.add(new_booking)
            db.session.commit()
            flash(f"Thank you, {name}! Your {room_type} booking request is received.", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Database Error: {str(e)}", "danger")
            return redirect(url_for('home'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
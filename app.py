import os
import random
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
import logging
from flask_babel import Babel, _
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'my-very-secret-key-123!'

# PostgreSQL configuration using SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Apple%402019%28%29@localhost:5432/queuemaster_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration for smtplib
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'queuemaster7275@gmail.com'
EMAIL_HOST_PASSWORD = 'yxwr ccrn luck uiah'
EMAIL_USE_TLS = True

# Babel configuration for multi-language support
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'es', 'fr']
babel = Babel(app)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

# Configure logging (console logging only)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('queue_app')

# Set up Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Global variable for pause status (kept for potential future use)
paused = False

# ------------------------
# Database Models using SQLAlchemy
# ------------------------
db = SQLAlchemy(app)

# User model - using only existing database columns
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    # Note: otp_created_at is removed as it doesn't exist in the database
    # Relationship to queue entries
    queue_entries = db.relationship('QueueEntry', backref='user', lazy=True)

# Queue Entry model
class QueueEntry(db.Model):
    __tablename__ = 'queue_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    person_name = db.Column(db.String(100), nullable=False)
    arrival_time = db.Column(db.DateTime, default=datetime.utcnow)
    served_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='waiting')  # waiting, served, cancelled
    priority = db.Column(db.String(20), default='normal')
    category = db.Column(db.String(50), default='general')
    order_index = db.Column(db.Integer, default=0)

# ------------------------
# User Loader
# ------------------------
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error("Error loading user: " + str(e))
        return None

# ------------------------
# Email Helper Functions
# ------------------------
def send_email(to_email, subject, body):
    """Send an email using smtplib"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        if EMAIL_USE_TLS:
            server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices('0123456789', k=6))

def send_otp_email(user):
    """Generate OTP, save it to user record, and send email"""
    otp = generate_otp()
    user.otp = otp
    db.session.commit()
    
    # Store OTP creation time in session instead of database
    session['otp_created_at'] = datetime.utcnow().timestamp()
    
    subject = _("Your Password Reset OTP")
    body = _(f"Hello {user.username},\n\nYour OTP for password reset is: {otp}\n\nThis OTP is valid for 10 minutes.\n\nIf you did not request this, please ignore this email.")
    
    return send_email(user.email, subject, body)

# ------------------------
# Routes for Authentication
# ------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not mobile or not password:
            flash(_('Please fill in all the fields.'), 'danger')
            return redirect(url_for('signup'))

        # Check if user exists
        if User.query.filter((User.username == username) | (User.email == email) | (User.mobile == mobile)).first():
            flash(_('Username, Email or Mobile already exists'), 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, mobile=mobile, password=hashed_password, is_verified=True)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(_('Account created! You can now log in.'), 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.exception("Error creating new user:")
            flash(_('An error occurred. Please try again.'), 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '').strip()
        remember = True if request.form.get('remember_me') == 'on' else False

        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash(_('Logged in successfully!'), 'success')
            return redirect(url_for('index'))
        else:
            flash(_('Invalid credentials'), 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('Logged out.'), 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        if user:
            if send_otp_email(user):
                flash(_('A 6-digit OTP has been sent to your email.'), "success")
                # Store user_id in session for later use
                session['reset_user_id'] = user.id
                return redirect(url_for('verify_otp'))
            else:
                flash(_('Error sending OTP. Please try again later.'), "danger")
        else:
            flash(_('Email not found.'), "danger")
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    # Get user_id from session
    user_id = session.get('reset_user_id')
    if not user_id:
        flash(_("Invalid request. Please start the password reset process again."), "danger")
        return redirect(url_for('forgot_password'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        
        # Check if OTP exists and is valid
        if user.otp and user.otp == entered_otp:
            # Check if OTP is expired (10 minutes validity)
            otp_created_at = session.get('otp_created_at')
            if otp_created_at:
                otp_age = datetime.utcnow().timestamp() - otp_created_at
                if otp_age <= 600:  # 10 minutes in seconds
                    # Clear the OTP after successful verification
                    user.otp = None
                    db.session.commit()
                    
                    # Keep user_id in session for the reset page
                    return redirect(url_for('reset_password'))
                else:
                    flash(_("OTP has expired. Please request a new one."), "danger")
                    return redirect(url_for('forgot_password'))
            else:
                flash(_("Session expired. Please request a new OTP."), "danger")
                return redirect(url_for('forgot_password'))
        else:
            flash(_("Invalid OTP. Please try again."), "danger")
    
    return render_template('verify_otp.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    # Get user_id from session
    user_id = session.get('reset_user_id')
    if not user_id:
        flash(_("Invalid request. Please start the password reset process again."), "danger")
        return redirect(url_for('forgot_password'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if password != confirm_password:
            flash(_("Passwords do not match."), 'danger')
            return render_template('reset_password.html')
        
        user.password = generate_password_hash(password)
        db.session.commit()
        
        # Clear session data
        session.pop('reset_user_id', None)
        session.pop('otp_created_at', None)
        
        flash(_("Your password has been updated. Please log in."), "success")
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

# ------------------------
# Routes for Queue Management
# ------------------------
@app.route('/')
@login_required
def index():
    logger.info(f"Index page accessed by: {current_user.username}")
    return render_template('index.html')

@app.route('/insert', methods=['POST'])
@login_required
def queue_insert():
    try:
        # Check that the form contains the expected key
        if 'element' not in request.form:
            logger.error("Form data missing 'element' key")
            return jsonify({"message": "Invalid form submission."}), 400

        person_name = request.form['element'].strip()
        logger.info(f"Received person name: '{person_name}' for user {current_user.username}")
        if not person_name:
            logger.warning("Insert attempt with empty name")
            return jsonify({"message": "Invalid name"}), 400

        max_order = db.session.query(db.func.max(QueueEntry.order_index))\
                    .filter(QueueEntry.user_id == current_user.id, QueueEntry.status == 'waiting')\
                    .scalar() or 0

        new_entry = QueueEntry(
            user_id=current_user.id,
            person_name=person_name,
            priority="normal",
            category="general",
            order_index=max_order + 1
        )

        db.session.add(new_entry)
        db.session.commit()
        logger.info(f"Inserted person '{person_name}' into the queue for user {current_user.username}")
        flash(f"{person_name} has been inserted into the queue", "success")
        return jsonify({"message": f"Inserted: {person_name}"})
    except Exception as e:
        logger.exception("Error inserting person:")
        return jsonify({"message": "Internal server error"}), 500

@app.route('/delete', methods=['POST'])
@login_required
def queue_delete():
    try:
        entry = QueueEntry.query.filter_by(user_id=current_user.id, status='waiting')\
                .order_by(QueueEntry.order_index).first()
        if not entry:
            logger.warning("Delete attempt on empty queue for user " + current_user.username)
            return jsonify({"message": "Queue Underflow"}), 400
        
        person_name = entry.person_name
        entry.status = 'served'
        entry.served_time = datetime.utcnow()
        db.session.commit()
        logger.info(f"Deleted (served) person '{person_name}' from the queue for user {current_user.username}")
        flash(f"{person_name} has been served and removed from the queue", "info")
        return jsonify({"message": f"Deleted: {person_name}"})
    except Exception as e:
        logger.exception("Error deleting person:")
        return jsonify({"message": "Internal server error"}), 500

@app.route('/display')
@login_required
def display_queue():
    try:
        entries = QueueEntry.query.filter_by(user_id=current_user.id, status='waiting')\
                    .order_by(QueueEntry.order_index).all()
        queue_list = [{"person_name": e.person_name, "priority": e.priority, "category": e.category} for e in entries]
        logger.info(f"Queue displayed for user {current_user.username}: {len(queue_list)} entries")
        return jsonify({"queue": queue_list})
    except Exception as e:
        logger.exception("Error displaying queue:")
        return jsonify({"message": "Internal server error"}), 500

@app.route('/analytics')
@login_required
def analytics():
    try:
        served_entries = QueueEntry.query.filter_by(user_id=current_user.id, status='served').all()
        total_served = len(served_entries)
        total_wait_time = sum(
            [(entry.served_time - entry.arrival_time).total_seconds() for entry in served_entries if entry.served_time],
            0
        )
        avg_wait_time = total_wait_time / total_served if total_served else 0

        served_details = []
        for entry in served_entries:
            served_details.append({
                "person_name": entry.person_name,
                "arrival_time": entry.arrival_time.isoformat() if entry.arrival_time else "N/A",
                "served_time": entry.served_time.isoformat() if entry.served_time else "N/A"
            })

        logger.info(f"Analytics accessed for user {current_user.username}: {total_served} served entries")
        return jsonify({
            "total_served": total_served,
            "avg_wait_time": round(avg_wait_time, 2),
            "served_details": served_details
        })
    except Exception as e:
        logger.exception("Error in analytics:")
        return jsonify({"message": "Internal server error"}), 500

# ------------------------
# Routes for User Profile
# ------------------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Minimal example: user can update their own username, email, and mobile.
    """
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        new_mobile = request.form.get('mobile', '').strip()

        if not new_username or not new_email or not new_mobile:
            flash(_('All fields are required.'), 'danger')
            return redirect(url_for('profile'))

        current_user.username = new_username
        current_user.email = new_email
        current_user.mobile = new_mobile
        db.session.commit()

        flash(_('Profile updated successfully!'), 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html')

if __name__ == '__main__':
    logger.info("Starting QueueMaster application...")
    app.run(debug=True)
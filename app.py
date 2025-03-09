import os
import random
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import logging
from flask_socketio import SocketIO, emit  # Added for WebSockets
from flask_babel import Babel, _        # For multi-language support
from twilio.rest import Client            # For SMS notifications

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-with-secure-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///queue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'queuemasterapp@gmail.com'
app.config['MAIL_PASSWORD'] = 'queuemasterapp@2019()'
app.config['MAIL_DEFAULT_SENDER'] = 'queuemasterapp@gmail.com'

# Babel configuration for multi-language support
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'es', 'fr']
def get_locale():
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])
babel = Babel(app, locale_selector=get_locale)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)
socketio = SocketIO(app)  # Initialize SocketIO

# Global variable for pause status
paused = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('queue_app')

# ------------------------
# Models
# ------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # For demo: plaintext (use hashing in production)
    is_verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)

class QueueEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))  # NEW: Phone number for SMS notifications
    arrival_time = db.Column(db.DateTime, default=datetime.utcnow)
    served_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='waiting')  # waiting, served, cancelled
    priority = db.Column(db.String(20), default='normal')   # new field
    category = db.Column(db.String(50), default='general')  # new field
    order_index = db.Column(db.Integer, default=0)          # new field for manual ordering

# ------------------------
# User Loader & DB Setup
# ------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    # Only run this code once
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                mobile='+10000000000',
                password='admin',
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
        app.db_initialized = True

# ------------------------
# Helper Functions for Password Reset
# ------------------------
def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except Exception:
        return None

# ------------------------
# WebSocket Events
# ------------------------
@socketio.on('connect')
def handle_connect():
    logger.info("Client connected to WebSocket")
    emit_queue_update()

def emit_queue_update():
    try:
        entries = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.order_index).all()
        queue_list = [{"person_name": e.person_name, "priority": e.priority, "category": e.category} for e in entries]
        waiting_count = len(queue_list)
        
        served_entries = QueueEntry.query.filter_by(status='served').all()
        total_served = len(served_entries)
        total_wait_time = sum([(s.served_time - s.arrival_time).total_seconds() for s in served_entries if s.served_time], 0)
        avg_wait_time = total_wait_time / total_served if total_served else 0
        
        socketio.emit('queue_update', {
            'queue': queue_list,
            'waiting_count': waiting_count,
            'analytics': {
                'total_served': total_served,
                'avg_wait_time': round(avg_wait_time, 2)
            }
        })
    except Exception as e:
        logger.error("Error emitting queue update: " + str(e))

# ------------------------
# Routes for Authentication
# ------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        mobile = request.form.get('mobile').strip()
        password = request.form.get('password').strip()
        if User.query.filter((User.username == username) | (User.email == email) | (User.mobile == mobile)).first():
            flash(_('Username, Email or Mobile already exists'), 'danger')
            return redirect(url_for('signup'))
        new_user = User(username=username, email=email, mobile=mobile, password=password, is_verified=True)
        db.session.add(new_user)
        db.session.commit()
        flash(_('Account created! You can now log in.'), 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email').strip()
        password = request.form.get('password').strip()
        remember = True if request.form.get('remember_me') == 'on' else False
        user = User.query.filter(
            ((User.username == username_or_email) | (User.email == username_or_email)) &
            (User.password == password)
        ).first()
        if user:
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
        email = request.form.get('email').strip()
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(email)
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Hi {user.username},\n\nTo reset your password, click the following link:\n{reset_url}\n\nIf you did not request a password reset, please ignore this email."
            try:
                mail.send(msg)
                flash(_('A reset link has been sent to your email.'), "success")
            except Exception as e:
                logger.error("Error sending reset email: " + str(e))
                flash(_('Error sending email. Please try again later.'), "danger")
        else:
            flash(_('Email not found.'), "danger")
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash(_("The reset link is invalid or has expired."), "danger")
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()
        if password != confirm_password:
            flash(_("Passwords do not match."), 'danger')
            return render_template('reset_password.html', token=token)
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = password
            db.session.commit()
            flash(_("Your password has been updated. Please log in."), "success")
            return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

# ------------------------
# Routes for Queue Management
# ------------------------
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/insert', methods=['POST'])
@login_required
def queue_insert():
    try:
        person_name = request.form['element']
        # Get phone number (optional)
        phone = request.form.get('phone', '').strip()
        if not person_name:
            return jsonify({"message": "Invalid name"}), 400
        max_order = db.session.query(db.func.max(QueueEntry.order_index)).filter(QueueEntry.status=='waiting').scalar() or 0
        new_entry = QueueEntry(
            person_name=person_name,
            phone=phone,
            priority="normal",
            category="general",
            order_index=max_order + 1
        )
        db.session.add(new_entry)
        db.session.commit()
        logger.info(f"Inserted person '{person_name}' into the queue")
        
        # Send SMS if phone number provided
        if phone:
            send_sms_notification(phone, f"Hi {person_name}, you have been added to the queue. Your turn is coming soon!")
        
        socketio.emit('notification', {
            'type': 'add',
            'message': f"{person_name} has been added to the queue"
        })
        emit_queue_update()
        
        return jsonify({"message": "Person inserted into the queue"})
    except Exception as e:
        logger.error("Error inserting person: " + str(e))
        return jsonify({"message": "Internal server error"}), 500

@app.route('/delete', methods=['POST'])
@login_required
def queue_delete():
    global paused
    if paused:
        return jsonify({"message": "Queue is paused. Cannot serve right now."}), 403
    try:
        entry = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.order_index).first()
        if not entry:
            return jsonify({"message": "Queue Underflow"}), 400
        
        person_name = entry.person_name
        entry.status = 'served'
        entry.served_time = datetime.utcnow()
        db.session.commit()
        logger.info(f"Deleted (served) person '{person_name}' from the queue")
        
        socketio.emit('notification', {
            'type': 'remove',
            'message': f"{person_name} has been served and removed from the queue"
        })
        emit_queue_update()
        
        return jsonify({"message": f"Deleted: {person_name}"})
    except Exception as e:
        logger.error("Error deleting person: " + str(e))
        return jsonify({"message": "Internal server error"}), 500

@app.route('/display')
@login_required
def display_queue():
    try:
        entries = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.order_index).all()
        queue_list = [{"person_name": e.person_name, "priority": e.priority, "category": e.category} for e in entries]
        return jsonify({"queue": queue_list})
    except Exception as e:
        logger.error("Error displaying queue: " + str(e))
        return jsonify({"message": "Internal server error"}), 500

@app.route('/analytics')
@login_required
def analytics():
    try:
        served_entries = QueueEntry.query.filter_by(status='served').all()
        total_served = len(served_entries)
        total_wait_time = sum([
            (entry.served_time - entry.arrival_time).total_seconds()
            for entry in served_entries if entry.served_time
        ], 0)
        avg_wait_time = total_wait_time / total_served if total_served else 0
        return jsonify({
            "total_served": total_served,
            "avg_wait_time": round(avg_wait_time, 2)
        })
    except Exception as e:
        logger.error("Error in analytics: " + str(e))
        return jsonify({"message": "Internal server error"}), 500

# ------------------------
# New Endpoints for Advanced Queue Management
# ------------------------
@app.route('/api/pause_queue', methods=['POST'])
@login_required
def pause_queue():
    global paused
    data = request.get_json()
    paused = data.get('pause', False)
    return jsonify({"message": f"Queue is now {'paused' if paused else 'active'}", "paused": paused})

@app.route('/api/set_priority', methods=['POST'])
@login_required
def set_priority():
    data = request.get_json()
    person_name = data.get('name')
    new_priority = data.get('priority', 'normal')
    entry = QueueEntry.query.filter_by(person_name=person_name, status='waiting').first()
    if entry:
        entry.priority = new_priority
        db.session.commit()
        return jsonify({"message": f"Priority for {person_name} set to {new_priority}."})
    else:
        return jsonify({"error": f"{person_name} not found in queue"}), 404

@app.route('/api/set_category', methods=['POST'])
@login_required
def set_category():
    data = request.get_json()
    person_name = data.get('name')
    category = data.get('category', 'general')
    entry = QueueEntry.query.filter_by(person_name=person_name, status='waiting').first()
    if entry:
        entry.category = category
        db.session.commit()
        return jsonify({"message": f"Category for {person_name} set to {category}."})
    else:
        return jsonify({"error": f"{person_name} not found in queue"}), 404

@app.route('/api/reorder_queue', methods=['POST'])
@login_required
def reorder_queue():
    data = request.get_json()
    new_order = data.get('new_order', [])
    waiting_entries = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.order_index).all()
    mapping = {e.person_name: e for e in waiting_entries}
    order = 1
    for name in new_order:
        if name in mapping:
            mapping[name].order_index = order
            order += 1
    db.session.commit()
    return jsonify({"message": "Queue reordered successfully!"})

# ========================
# NEW CODE FOR USER PROFILE
# ========================
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

# ------------------------
# SMS Notification Function using Twilio
# ------------------------
from twilio.rest import Client

def send_sms_notification(phone, message):
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
    if not (account_sid and auth_token and twilio_number):
        logger.error("Twilio credentials not properly configured.")
        return
    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=twilio_number,
            to=phone
        )
        logger.info(f"SMS sent to {phone}: {message}")
    except Exception as ex:
        logger.error("Failed to send SMS: " + str(ex))

if __name__ == '__main__':
    socketio.run(app, debug=True)

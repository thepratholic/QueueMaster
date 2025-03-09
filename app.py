# import random
# from datetime import datetime
# from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# from flask_mail import Mail, Message
# from itsdangerous import URLSafeTimedSerializer
# import logging

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'replace-with-secure-key'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///queue.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Email configuration
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'queuemasterapp@gmail.com'
# app.config['MAIL_PASSWORD'] = 'queuemasterapp@2019()'
# app.config['MAIL_DEFAULT_SENDER'] = 'queuemasterapp@gmail.com'

# db = SQLAlchemy(app)
# login_manager = LoginManager(app)
# login_manager.login_view = 'login'
# mail = Mail(app)

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger('queue_app')


# # ------------------------
# # Models
# # ------------------------
# class User(UserMixin, db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     mobile = db.Column(db.String(20), unique=True, nullable=False)
#     password = db.Column(db.String(200), nullable=False)  # For demo: plaintext (use hashing in production)
#     is_verified = db.Column(db.Boolean, default=False)
#     # Removed OTP field usage, but kept for schema if needed in future
#     otp = db.Column(db.String(6), nullable=True)


# class QueueEntry(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     person_name = db.Column(db.String(100), nullable=False)
#     arrival_time = db.Column(db.DateTime, default=datetime.utcnow)
#     served_time = db.Column(db.DateTime)
#     status = db.Column(db.String(20), default='waiting')  # waiting, served, cancelled


# # ------------------------
# # User Loader & DB Setup
# # ------------------------
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

# @app.before_request
# def create_tables():
#     # Only create tables if they don't exist; do not drop existing tables.
#     db.create_all()
#     # Create a default admin user if not exists.
#     if not User.query.filter_by(username='admin').first():
#         admin = User(username='admin', email='admin@example.com', mobile='+10000000000', password='admin', is_verified=True)
#         db.session.add(admin)
#         db.session.commit()


# # ------------------------
# # Helper Functions for Password Reset
# # ------------------------
# def generate_reset_token(email):
#     serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
#     return serializer.dumps(email, salt='password-reset-salt')


# def verify_reset_token(token, expiration=3600):
#     serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
#     try:
#         email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
#         return email
#     except Exception:
#         return None


# # ------------------------
# # Routes for Authentication
# # ------------------------

# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         username = request.form.get('username').strip()
#         email = request.form.get('email').strip()
#         mobile = request.form.get('mobile').strip()
#         password = request.form.get('password').strip()
#         if User.query.filter((User.username == username) | (User.email == email) | (User.mobile == mobile)).first():
#             flash('Username, Email or Mobile already exists', 'danger')
#             return redirect(url_for('signup'))
#         # Create new user and mark as verified (OTP removed)
#         new_user = User(username=username, email=email, mobile=mobile, password=password, is_verified=True)
#         db.session.add(new_user)
#         db.session.commit()
#         flash('Account created! You can now log in.', 'success')
#         return redirect(url_for('login'))
#     return render_template('signup.html')


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username_or_email = request.form.get('username_or_email').strip()
#         password = request.form.get('password').strip()
#         remember = True if request.form.get('remember_me') == 'on' else False
#         user = User.query.filter(
#             ((User.username == username_or_email) | (User.email == username_or_email)) &
#             (User.password == password)
#         ).first()
#         if user:
#             # Since OTP is removed, user.is_verified is assumed True.
#             login_user(user, remember=remember)
#             flash('Logged in successfully!', 'success')
#             return redirect(url_for('index'))
#         else:
#             flash('Invalid credentials', 'danger')
#     return render_template('login.html')


# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('Logged out.', 'info')
#     return redirect(url_for('login'))


# # ------------------------
# # Forgot Password & Reset Password Routes
# # ------------------------
# @app.route('/forgot-password', methods=['GET', 'POST'])
# def forgot_password():
#     if request.method == 'POST':
#         email = request.form.get('email').strip()
#         user = User.query.filter_by(email=email).first()
#         if user:
#             token = generate_reset_token(email)
#             reset_url = url_for('reset_password', token=token, _external=True)
#             msg = Message("Password Reset Request", recipients=[email])
#             msg.body = f"Hi {user.username},\n\nTo reset your password, click the following link:\n{reset_url}\n\nIf you did not request a password reset, please ignore this email."
#             try:
#                 mail.send(msg)
#                 flash("A reset link has been sent to your email.", "success")
#             except Exception as e:
#                 logger.error("Error sending reset email: " + str(e))
#                 flash("Error sending email. Please try again later.", "danger")
#         else:
#             flash("Email not found.", "danger")
#         return redirect(url_for('login'))
#     return render_template('forgot_password.html')


# @app.route('/reset-password/<token>', methods=['GET', 'POST'])
# def reset_password(token):
#     email = verify_reset_token(token)
#     if not email:
#         flash("The reset link is invalid or has expired.", "danger")
#         return redirect(url_for('forgot_password'))
#     if request.method == 'POST':
#         password = request.form.get('password').strip()
#         confirm_password = request.form.get('confirm_password').strip()
#         if password != confirm_password:
#             flash("Passwords do not match.", "danger")
#             return render_template('reset_password.html', token=token)
#         user = User.query.filter_by(email=email).first()
#         if user:
#             user.password = password  # In production, be sure to hash the password!
#             db.session.commit()
#             flash("Your password has been updated. Please log in.", "success")
#             return redirect(url_for('login'))
#     return render_template('reset_password.html', token=token)


# # ------------------------
# # Routes for Queue Management
# # ------------------------
# @app.route('/')
# @login_required
# def index():
#     return render_template('index.html')


# @app.route('/insert', methods=['POST'])
# @login_required
# def queue_insert():
#     try:
#         person_name = request.form['element']
#         if not person_name:
#             return jsonify({"message": "Invalid name"}), 400
#         new_entry = QueueEntry(person_name=person_name)
#         db.session.add(new_entry)
#         db.session.commit()
#         logger.info(f"Inserted person '{person_name}' into the queue")
#         return jsonify({"message": "Person inserted into the queue"})
#     except Exception as e:
#         logger.error("Error inserting person: " + str(e))
#         return jsonify({"message": "Internal server error"}), 500


# @app.route('/delete', methods=['POST'])
# @login_required
# def queue_delete():
#     try:
#         entry = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.arrival_time).first()
#         if not entry:
#             return jsonify({"message": "Queue Underflow"}), 400
#         entry.status = 'served'
#         entry.served_time = datetime.utcnow()
#         db.session.commit()
#         logger.info(f"Deleted (served) person '{entry.person_name}' from the queue")
#         return jsonify({"message": f"Deleted: {entry.person_name}"})
#     except Exception as e:
#         logger.error("Error deleting person: " + str(e))
#         return jsonify({"message": "Internal server error"}), 500


# @app.route('/display')
# @login_required
# def display_queue():
#     try:
#         entries = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.arrival_time).all()
#         queue_list = [entry.person_name for entry in entries]
#         return jsonify({"queue": queue_list})
#     except Exception as e:
#         logger.error("Error displaying queue: " + str(e))
#         return jsonify({"message": "Internal server error"}), 500


# @app.route('/analytics')
# @login_required
# def analytics():
#     try:
#         served_entries = QueueEntry.query.filter_by(status='served').all()
#         total_served = len(served_entries)
#         total_wait_time = sum([(entry.served_time - entry.arrival_time).total_seconds() for entry in served_entries if entry.served_time], 0)
#         avg_wait_time = total_wait_time / total_served if total_served else 0
#         return jsonify({
#             "total_served": total_served,
#             "avg_wait_time": round(avg_wait_time, 2)
#         })
#     except Exception as e:
#         logger.error("Error in analytics: " + str(e))
#         return jsonify({"message": "Internal server error"}), 500


# if __name__ == '__main__':
#     app.run(debug=True)


import random
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import logging
from flask_socketio import SocketIO, emit  # Added for WebSockets

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

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)
socketio = SocketIO(app)  # Initialize SocketIO

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
    # Removed OTP field usage, but kept for schema if needed in future
    otp = db.Column(db.String(6), nullable=True)


class QueueEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_name = db.Column(db.String(100), nullable=False)
    arrival_time = db.Column(db.DateTime, default=datetime.utcnow)
    served_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='waiting')  # waiting, served, cancelled


# ------------------------
# User Loader & DB Setup
# ------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    # Only create tables if they don't exist; do not drop existing tables.
    db.create_all()
    # Create a default admin user if not exists.
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', mobile='+10000000000', password='admin', is_verified=True)
        db.session.add(admin)
        db.session.commit()


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
    # Send initial queue data upon connection
    emit_queue_update()


def emit_queue_update():
    """Helper function to emit queue updates to all connected clients"""
    try:
        # Get current queue data
        entries = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.arrival_time).all()
        queue_list = [entry.person_name for entry in entries]
        waiting_count = len(queue_list)
        
        # Get analytics data
        served_entries = QueueEntry.query.filter_by(status='served').all()
        total_served = len(served_entries)
        total_wait_time = sum([(entry.served_time - entry.arrival_time).total_seconds() for entry in served_entries if entry.served_time], 0)
        avg_wait_time = total_wait_time / total_served if total_served else 0
        
        # Emit the update to all connected clients
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
            flash('Username, Email or Mobile already exists', 'danger')
            return redirect(url_for('signup'))
        # Create new user and mark as verified (OTP removed)
        new_user = User(username=username, email=email, mobile=mobile, password=password, is_verified=True)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
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
            # Since OTP is removed, user.is_verified is assumed True.
            login_user(user, remember=remember)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))


# ------------------------
# Forgot Password & Reset Password Routes
# ------------------------
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
                flash("A reset link has been sent to your email.", "success")
            except Exception as e:
                logger.error("Error sending reset email: " + str(e))
                flash("Error sending email. Please try again later.", "danger")
        else:
            flash("Email not found.", "danger")
        return redirect(url_for('login'))
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html', token=token)
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = password  # In production, be sure to hash the password!
            db.session.commit()
            flash("Your password has been updated. Please log in.", "success")
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
        if not person_name:
            return jsonify({"message": "Invalid name"}), 400
        new_entry = QueueEntry(person_name=person_name)
        db.session.add(new_entry)
        db.session.commit()
        logger.info(f"Inserted person '{person_name}' into the queue")
        
        # Emit WebSocket update with notification
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
    try:
        entry = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.arrival_time).first()
        if not entry:
            return jsonify({"message": "Queue Underflow"}), 400
        
        person_name = entry.person_name
        entry.status = 'served'
        entry.served_time = datetime.utcnow()
        db.session.commit()
        logger.info(f"Deleted (served) person '{person_name}' from the queue")
        
        # Emit WebSocket update with notification
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
        entries = QueueEntry.query.filter_by(status='waiting').order_by(QueueEntry.arrival_time).all()
        queue_list = [entry.person_name for entry in entries]
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
        total_wait_time = sum([(entry.served_time - entry.arrival_time).total_seconds() for entry in served_entries if entry.served_time], 0)
        avg_wait_time = total_wait_time / total_served if total_served else 0
        return jsonify({
            "total_served": total_served,
            "avg_wait_time": round(avg_wait_time, 2)
        })
    except Exception as e:
        logger.error("Error in analytics: " + str(e))
        return jsonify({"message": "Internal server error"}), 500


if __name__ == '__main__':
    socketio.run(app, debug=True)  # Use socketio.run instead of app.run
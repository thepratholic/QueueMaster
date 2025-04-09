import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import logging
from flask_babel import Babel, _
from pymongo import MongoClient
from bson.objectid import ObjectId
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    # Fallback with warning
    username = os.getenv('MONGO_USERNAME')
    password = os.getenv('MONGO_PASSWORD')
    if username and password:
        username = quote_plus(username)
        password = quote_plus(password)
        MONGODB_URI = f"mongodb+srv://{username}:{password}@queuemaster-cluster.uyawvvr.mongodb.net/queuemaster?retryWrites=true&w=majority"
    else:
        raise ValueError("MongoDB credentials not found. Set MONGODB_URI or MONGO_USERNAME and MONGO_PASSWORD")

client = MongoClient(MONGODB_URI)
mongo_db = client['queuemaster']

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Babel configuration for multi-language support
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'es', 'fr']

def get_locale():
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

babel = Babel(app, locale_selector=get_locale)

# Configure logging (only to console; no file logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('queue_app')

# Flask-Login and Mail setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Global variable for pause status (kept for potential future use)
paused = False

# ------------------------
# MongoDB User Model
# ------------------------
class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        
    def get_id(self):
        return str(self.user_data.get('_id'))
        
    @property
    def id(self):
        return str(self.user_data.get('_id'))
        
    @property
    def username(self):
        return self.user_data.get('username')
        
    @username.setter
    def username(self, value):
        self.user_data['username'] = value
        
    @property
    def email(self):
        return self.user_data.get('email')
        
    @email.setter
    def email(self, value):
        self.user_data['email'] = value
        
    @property
    def mobile(self):
        return self.user_data.get('mobile')
        
    @mobile.setter
    def mobile(self, value):
        self.user_data['mobile'] = value
        
    @property
    def password(self):
        return self.user_data.get('password')
        
    @password.setter
    def password(self, value):
        self.user_data['password'] = value
        
    @property
    def is_verified(self):
        return self.user_data.get('is_verified', False)
    
    @property
    def otp(self):
        return self.user_data.get('otp')

# ------------------------
# User Loader
# ------------------------
@login_manager.user_loader
def load_user(user_id):
    user_data = mongo_db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# ------------------------
# Database Initialization
# ------------------------
@app.before_request
def initialize_db():
    if not hasattr(app, 'db_initialized'):
        try:
            logger.info("Checking database initialization...")
            # Create indexes for faster queries
            mongo_db.users.create_index('username', unique=True)
            mongo_db.users.create_index('email', unique=True)
            mongo_db.users.create_index('mobile', unique=True)
            
            # Check if admin user exists, if not create one
            admin = mongo_db.users.find_one({'username': 'admin'})
            if not admin:
                logger.info("Creating admin user...")
                admin_user = {
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'mobile': '+10000000000',
                    'password': 'admin',  # In production, use password hashing
                    'is_verified': True,
                    'created_at': datetime.utcnow()
                }
                mongo_db.users.insert_one(admin_user)
                logger.info("Admin user created successfully")
            
            app.db_initialized = True
            logger.info("Database initialization complete")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")

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
# Debug Routes (for admin use)
# ------------------------
@app.route('/debug/users')
@login_required
def debug_users():
    if not current_user.username == 'admin':
        logger.warning(f"Unauthorized access to debug/users by {current_user.username}")
        return jsonify({"message": "Not authorized"}), 403
    
    users = list(mongo_db.users.find({}, {'password': 0}))  # Exclude password
    user_list = [{
        "id": str(user['_id']),
        "username": user['username'],
        "email": user['email'],
        "mobile": user['mobile'],
        "is_verified": user.get('is_verified', False)
    } for user in users]
    
    logger.info(f"Debug users accessed: {len(user_list)} users found")
    return jsonify(user_list)

@app.route('/debug/queue')
@login_required
def debug_queue():
    if not current_user.username == 'admin':
        logger.warning(f"Unauthorized access to debug/queue by {current_user.username}")
        return jsonify({"message": "Not authorized"}), 403
    
    entries = list(mongo_db.queue.find({}))
    entry_list = [{
        "id": str(entry['_id']),
        "person_name": entry['person_name'],
        "status": entry['status'],
        "priority": entry['priority'],
        "category": entry['category'],
        "order_index": entry['order_index'],
        "arrival_time": entry['arrival_time'].isoformat() if 'arrival_time' in entry else None,
        "served_time": entry['served_time'].isoformat() if 'served_time' in entry else None
    } for entry in entries]
    
    logger.info(f"Debug queue accessed: {len(entry_list)} entries found")
    return jsonify(entry_list)

@app.route('/debug/db-info')
@login_required
def debug_db_info():
    if not current_user.username == 'admin':
        logger.warning(f"Unauthorized access to debug/db-info by {current_user.username}")
        return jsonify({"message": "Not authorized"}), 403
    
    try:
        collections = mongo_db.list_collection_names()
        collection_stats = {}
        for collection in collections:
            count = mongo_db[collection].count_documents({})
            collection_stats[collection] = count
            
        info = {
            "database_type": "MongoDB",
            "database_name": mongo_db.name,
            "collections": collections,
            "collection_stats": collection_stats
        }
        
        logger.info(f"Database info accessed: {len(collections)} collections found")
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting database info: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
        
        existing_user = mongo_db.users.find_one({
            '$or': [
                {'username': username},
                {'email': email},
                {'mobile': mobile}
            ]
        })
        
        if existing_user:
            flash(_('Username, Email or Mobile already exists'), 'danger')
            logger.warning(f"Signup failed: Email {email} or username {username} already exists")
            return redirect(url_for('signup'))
        
        try:
            new_user = {
                'username': username,
                'email': email,
                'mobile': mobile,
                'password': password,  # In production, use password hashing
                'is_verified': True,
                'created_at': datetime.utcnow()
            }
            result = mongo_db.users.insert_one(new_user)
            logger.info(f"New user created: {username} (ID: {result.inserted_id})")
            flash(_('Account created! You can now log in.'), 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            flash(_('An error occurred. Please try again.'), 'danger')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email').strip()
        password = request.form.get('password').strip()
        remember = True if request.form.get('remember_me') == 'on' else False
        
        user_data = mongo_db.users.find_one({
            '$and': [
                {'$or': [{'username': username_or_email}, {'email': username_or_email}]},
                {'password': password}
            ]
        })
        
        if user_data:
            user = User(user_data)
            login_user(user, remember=remember)
            logger.info(f"User logged in: {user.username} (ID: {user.id})")
            flash(_('Logged in successfully!'), 'success')
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username/email: {username_or_email}")
            flash(_('Invalid credentials'), 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f"User logged out: {current_user.username} (ID: {current_user.id})")
    logout_user()
    flash(_('Logged out.'), 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        user_data = mongo_db.users.find_one({'email': email})
        
        if user_data:
            token = generate_reset_token(email)
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Hi {user_data['username']},\n\nTo reset your password, click the following link:\n{reset_url}\n\nIf you did not request a password reset, please ignore this email."
            
            try:
                mail.send(msg)
                logger.info(f"Password reset email sent to: {email}")
                flash(_('A reset link has been sent to your email.'), "success")
            except Exception as e:
                logger.error(f"Error sending reset email to {email}: {str(e)}")
                flash(_('Error sending email. Please try again later.'), "danger")
        else:
            logger.warning(f"Password reset attempted for non-existent email: {email}")
            flash(_('Email not found.'), "danger")
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        logger.warning("Invalid or expired password reset token used")
        flash(_("The reset link is invalid or has expired."), "danger")
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()
        
        if password != confirm_password:
            flash(_("Passwords do not match."), 'danger')
            return render_template('reset_password.html', token=token)
        
        user_data = mongo_db.users.find_one({'email': email})
        if user_data:
            mongo_db.users.update_one(
                {'_id': user_data['_id']},
                {'$set': {'password': password}}
            )
            logger.info(f"Password reset successful for: {email}")
            flash(_("Your password has been updated. Please log in."), "success")
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

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
        person_name = request.form['element']
        logger.info(f"Received name: '{person_name}'")
        if not person_name:
            logger.warning("Insert attempt with empty name")
            return jsonify({"message": "Invalid name"}), 400
        
        max_order_result = mongo_db.queue.find_one(
            {'status': 'waiting'},
            sort=[('order_index', -1)]
        )
        max_order = max_order_result['order_index'] if max_order_result else 0
        
        new_entry = {
            'person_name': person_name,
            'priority': "normal",
            'category': "general",
            'order_index': max_order + 1,
            'status': 'waiting',
            'arrival_time': datetime.utcnow()
        }
        
        result = mongo_db.queue.insert_one(new_entry)
        inserted_doc = mongo_db.queue.find_one({'_id': result.inserted_id})
        logger.info(f"Inserted person '{person_name}' into the queue with ID: {result.inserted_id}")
        
        flash(f"{person_name} has been inserted into the queue", "success")
        return jsonify({"message": "Person inserted into the queue"})
    except Exception as e:
        logger.error(f"Error inserting person: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@app.route('/delete', methods=['POST'])
@login_required
def queue_delete():
    try:
        entry = mongo_db.queue.find_one(
            {'status': 'waiting'},
            sort=[('order_index', 1)]
        )
        
        if not entry:
            logger.warning("Delete attempt on empty queue")
            return jsonify({"message": "Queue Underflow"}), 400
        
        person_name = entry['person_name']
        mongo_db.queue.update_one(
            {'_id': entry['_id']},
            {
                '$set': {
                    'status': 'served',
                    'served_time': datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Deleted (served) person '{person_name}' from the queue (ID: {entry['_id']})")
        flash(f"{person_name} has been served and removed from the queue", "info")
        return jsonify({"message": f"Deleted: {person_name}"})
    except Exception as e:
        logger.error(f"Error deleting person: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@app.route('/display')
@login_required
def display_queue():
    try:
        entries = list(mongo_db.queue.find({'status': 'waiting'}).sort('order_index', 1))
        queue_list = [{"person_name": e['person_name'], "priority": e['priority'], "category": e['category']} for e in entries]
        logger.info(f"Queue displayed: {len(queue_list)} entries")
        return jsonify({"queue": queue_list})
    except Exception as e:
        logger.error(f"Error displaying queue: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@app.route('/analytics')
@login_required
def analytics():
    try:
        served_entries = list(mongo_db.queue.find({'status': 'served'}))
        total_served = len(served_entries)
        
        total_wait_time = 0
        served_details = []
        for entry in served_entries:
            arrival_str = entry['arrival_time'].isoformat() if 'arrival_time' in entry else "N/A"
            served_str = entry['served_time'].isoformat() if 'served_time' in entry else "N/A"
            
            if 'served_time' in entry and entry['served_time'] and 'arrival_time' in entry and entry['arrival_time']:
                wait_time = (entry['served_time'] - entry['arrival_time']).total_seconds()
                total_wait_time += wait_time
            
            served_details.append({
                "person_name": entry['person_name'],
                "arrival_time": arrival_str,
                "served_time": served_str
            })
        
        avg_wait_time = total_wait_time / total_served if total_served else 0
        
        logger.info(f"Analytics accessed: {total_served} served entries")
        return jsonify({
            "total_served": total_served,
            "avg_wait_time": round(avg_wait_time, 2),
            "served_details": served_details
        })
    except Exception as e:
        logger.error(f"Error in analytics: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

# ------------------------
# User Profile
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

        try:
            mongo_db.users.update_one(
                {'_id': ObjectId(current_user.id)},
                {
                    '$set': {
                        'username': new_username,
                        'email': new_email,
                        'mobile': new_mobile
                    }
                }
            )
            logger.info(f"User profile updated: {current_user.id}")
            flash(_('Profile updated successfully!'), 'success')
        except Exception as e:
            logger.error(f"Error updating profile for user {current_user.id}: {str(e)}")
            flash(_('Error updating profile. Please try again.'), 'danger')
            
        return redirect(url_for('profile'))

    return render_template('profile.html')

# Root route handler for Vercel
@app.route('/api/healthcheck')
def healthcheck():
    return jsonify({
        "status": "ok", 
        "message": "QueueMaster is running",
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    # For local development only
    app.run(debug=True)
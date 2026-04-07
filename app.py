from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from dotenv import load_dotenv
import hashlib
import json
import sqlite3
import os
from time import time
from blockchain_voting_system import Blockchain

# --- 1. CONFIGURATION & SECURITY ---
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load Secret Key from .env (Safety fallback provided for dev)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_fallback_key_do_not_use_in_prod')

# Auto-Logout after 5 minutes of inactivity
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

DB_NAME = "users.db"

def init_db():
    """Creates the User table if it doesn't exist"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db() # Run once on startup

# --- 2. USER AUTHENTICATION MODELS ---
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(id=user_data[0], username=user_data[1], password=user_data[2])
    return None

def load_candidates(filename='names.txt'):
    base = os.path.dirname(__file__)
    path = os.path.join(base, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return ["Candidate A", "Candidate B"]

CANDIDATES = load_candidates()
blockchain = Blockchain()

# --- 4. ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash("Username already taken.", "danger")
            else:
                # Hash password before saving
                hashed_pw = generate_password_hash(password, method='scrypt')
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
                conn.commit()
                flash("Account created! Please login.", "success")
                return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user_data = cursor.fetchone()
            
            if user_data and check_password_hash(user_data[2], password):
                user_obj = User(id=user_data[0], username=user_data[1], password=user_data[2])
                login_user(user_obj)
                
                # Activate 5-minute timer
                session.permanent = True
                
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for('index'))
            else:
                flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    vote_counts = blockchain.tally_votes(CANDIDATES)
    return render_template('index.html', 
                           chain=blockchain.chain, 
                           pending=blockchain.pending_votes,
                           candidates=CANDIDATES,
                           vote_counts=vote_counts,
                           user=current_user)

@app.route('/vote', methods=['POST'])
@login_required
def vote():
    voter_id = current_user.username
    candidate = request.form.get('candidate')
    
    if candidate:
        success = blockchain.new_vote(voter_id, candidate)
        if success:
            flash(f"Vote cast for {candidate} successfully!", "success")
        else:
            flash(f"ERROR: {voter_id}, you have already voted!", "danger")
    else:
        flash("Error: Missing Candidate selection.", "warning")
            
    return redirect(url_for('index'))

@app.route('/mine', methods=['GET'])
@login_required
def mine():
    if not blockchain.pending_votes:
        flash("No votes to mine.", "warning")
        return redirect(url_for('index'))

    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block['proof'])
    previous_hash = blockchain.hash(last_block)
    blockchain.new_block(proof, previous_hash)
    
    flash("Block mined successfully! Votes are now immutable.", "success")
    return redirect(url_for('index'))

@app.route('/validate', methods=['GET'])
def validate():
    if blockchain.is_chain_valid(blockchain.chain):
        flash("System Secure: Blockchain integrity verified.", "success")
    else:
        flash("SECURITY ALERT: Blockchain has been tampered with!", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False, port=5000)
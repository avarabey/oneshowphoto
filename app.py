from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.urls import quote as url_quote  # Changed from direct import of url_quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SERVER_NAME'] = 'varabey.online'  # Add this line

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    photos = db.relationship('Photo', backref='user', lazy=True)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    share_token = db.Column(db.String(100), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    views = db.relationship('PhotoView', backref='photo', lazy=True)

class PhotoView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'photo' not in request.files:
        flash('No photo uploaded')
        return redirect(url_for('dashboard'))
    
    photo = request.files['photo']
    if photo.filename == '':
        flash('No photo selected')
        return redirect(url_for('dashboard'))
    
    if photo:
        filename = str(uuid.uuid4()) + os.path.splitext(photo.filename)[1]
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_photo = Photo(
            filename=filename,
            original_filename=photo.filename,
            share_token=str(uuid.uuid4()),
            user_id=current_user.id
        )
        db.session.add(new_photo)
        db.session.commit()
        
    return redirect(url_for('dashboard'))

@app.route('/share/<token>')
def share(token):
    photo = Photo.query.filter_by(share_token=token).first_or_404()
    
    view = PhotoView(
        photo_id=photo.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        referrer=request.referrer
    )
    db.session.add(view)
    db.session.commit()
    
    return render_template('share.html', photo=photo)

@app.route('/photo/<token>')
def get_photo(token):
    photo = Photo.query.filter_by(share_token=token).first_or_404()
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], photo.filename),
        mimetype='image/jpeg',
        as_attachment=False
    )

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', photos=current_user.photos)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
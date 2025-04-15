from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime
import json
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    share_token_2 = db.Column(db.String(100), unique=True)
    share_token_3 = db.Column(db.String(100), unique=True)
    share_token_4 = db.Column(db.String(100), unique=True)
    token_used = db.Column(db.Boolean, default=False)
    token_2_used = db.Column(db.Boolean, default=False)
    token_3_used = db.Column(db.Boolean, default=False)
    token_4_used = db.Column(db.Boolean, default=False)
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

@app.route('/')
def index():
    return redirect(url_for('login'))

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
            share_token_2=str(uuid.uuid4()),
            share_token_3=str(uuid.uuid4()),
            share_token_4=str(uuid.uuid4()),
            user_id=current_user.id
        )
        db.session.add(new_photo)
        db.session.commit()
        
    return redirect(url_for('dashboard'))

@app.route('/share/<token>')
def share(token):
    # Ищем фото по любому из четырех токенов
    photo = Photo.query.filter(
        ((Photo.share_token == token) & (Photo.token_used == False)) | 
        ((Photo.share_token_2 == token) & (Photo.token_2_used == False)) | 
        ((Photo.share_token_3 == token) & (Photo.token_3_used == False)) | 
        ((Photo.share_token_4 == token) & (Photo.token_4_used == False))
    ).first_or_404()
    
    # Отмечаем токен как использованный
    if photo.share_token == token:
        photo.token_used = True
    elif photo.share_token_2 == token:
        photo.token_2_used = True
    elif photo.share_token_3 == token:
        photo.token_3_used = True
    elif photo.share_token_4 == token:
        photo.token_4_used = True
    
    view = PhotoView(
        photo_id=photo.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        referrer=request.referrer
    )
    db.session.add(view)
    db.session.commit()
    
    return render_template('share.html', photo=photo, token=token, ip_address=request.remote_addr)

@app.route('/photo/<token>')
def get_photo(token):
    # Ищем фото по любому из четырех токенов
    photo = Photo.query.filter(
        (Photo.share_token == token) | 
        (Photo.share_token_2 == token) | 
        (Photo.share_token_3 == token) | 
        (Photo.share_token_4 == token)
    ).first_or_404()
    
    # Открываем изображение и добавляем водяной знак
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
    img = Image.open(img_path)
    
    # Добавляем водяной знак с IP-адресом
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()
    
    watermark_text = f"IP: {request.remote_addr}"
    text_width, text_height = draw.textsize(watermark_text, font=font)
    position = (img.width - text_width - 10, img.height - text_height - 10)
    
    # Полупрозрачный фон для текста
    draw.rectangle(
        [(position[0] - 5, position[1] - 5), 
         (position[0] + text_width + 5, position[1] + text_height + 5)], 
        fill=(0, 0, 0, 128)
    )
    draw.text(position, watermark_text, fill=(255, 255, 255, 255), font=font)
    
    # Сохраняем изображение во временный буфер
    img_io = io.BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    
    return send_file(
        img_io,
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
    app.run(host='0.0.0.0', port=5000, debug=False)  # Слушаем на всех интерфейсах
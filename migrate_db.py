from app import app, db

with app.app_context():
    # Добавляем новые колонки
    db.engine.execute('ALTER TABLE photo ADD COLUMN share_token_2 VARCHAR(100) UNIQUE')
    db.engine.execute('ALTER TABLE photo ADD COLUMN share_token_3 VARCHAR(100) UNIQUE')
    db.engine.execute('ALTER TABLE photo ADD COLUMN share_token_4 VARCHAR(100) UNIQUE')
    
    # Обновляем существующие записи
    from app import Photo
    import uuid
    
    photos = Photo.query.all()
    for photo in photos:
        photo.share_token_2 = str(uuid.uuid4())
        photo.share_token_3 = str(uuid.uuid4())
        photo.share_token_4 = str(uuid.uuid4())
    
    db.session.commit()
    print("Database migration completed successfully!")
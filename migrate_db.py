from app import app, db
import uuid
from sqlalchemy import text

with app.app_context():
    # Добавляем новые колонки с использованием text()
    db.session.execute(text('ALTER TABLE photo ADD COLUMN share_token_2 VARCHAR(100) UNIQUE'))
    db.session.execute(text('ALTER TABLE photo ADD COLUMN share_token_3 VARCHAR(100) UNIQUE'))
    db.session.execute(text('ALTER TABLE photo ADD COLUMN share_token_4 VARCHAR(100) UNIQUE'))
    db.session.commit()
    
    # Обновляем существующие записи
    from app import Photo
    
    photos = Photo.query.all()
    for photo in photos:
        photo.share_token_2 = str(uuid.uuid4())
        photo.share_token_3 = str(uuid.uuid4())
        photo.share_token_4 = str(uuid.uuid4())
    
    db.session.commit()
    print("Миграция базы данных успешно завершена!")
from app import app, db
import uuid
from sqlalchemy import text
import sqlalchemy.exc

with app.app_context():
    # Добавляем новые колонки с использованием text()
    try:
        db.session.execute(text('ALTER TABLE photo ADD COLUMN share_token_2 VARCHAR(100) UNIQUE'))
        db.session.execute(text('ALTER TABLE photo ADD COLUMN share_token_3 VARCHAR(100) UNIQUE'))
        db.session.execute(text('ALTER TABLE photo ADD COLUMN share_token_4 VARCHAR(100) UNIQUE'))
        db.session.commit()
        print("Колонки успешно добавлены")
    except sqlalchemy.exc.OperationalError as e:
        print(f"Ошибка при добавлении колонок: {e}")
        db.session.rollback()
    
    # Обновляем существующие записи
    try:
        from app import Photo
        
        photos = Photo.query.all()
        for photo in photos:
            if not photo.share_token_2:
                photo.share_token_2 = str(uuid.uuid4())
            if not photo.share_token_3:
                photo.share_token_3 = str(uuid.uuid4())
            if not photo.share_token_4:
                photo.share_token_4 = str(uuid.uuid4())
        
        db.session.commit()
        print("Записи успешно обновлены")
    except Exception as e:
        print(f"Ошибка при обновлении записей: {e}")
        db.session.rollback()
    
    print("Миграция базы данных завершена")
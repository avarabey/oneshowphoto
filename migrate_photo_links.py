from app import app, db
from sqlalchemy import text
import sqlalchemy.exc

with app.app_context():
    try:
        # Создаем таблицу для дополнительных ссылок
        db.session.execute(text('''
            CREATE TABLE photo_link (
                id INTEGER PRIMARY KEY,
                photo_id INTEGER NOT NULL,
                token VARCHAR(100) UNIQUE NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(photo_id) REFERENCES photo(id)
            )
        '''))
        
        db.session.commit()
        print("Таблица photo_link успешно создана")
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")
        db.session.rollback()
    
    print("Миграция базы данных завершена")
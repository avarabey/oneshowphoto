from app import app, db
import uuid
from sqlalchemy import text
import sqlalchemy.exc

with app.app_context():
    try:
        # Добавляем колонки для отслеживания использования токенов
        db.session.execute(text('''
            CREATE TABLE photo_new (
                id INTEGER PRIMARY KEY,
                filename VARCHAR(200) NOT NULL,
                original_filename VARCHAR(200) NOT NULL,
                share_token VARCHAR(100) UNIQUE,
                share_token_2 VARCHAR(100) UNIQUE,
                share_token_3 VARCHAR(100) UNIQUE,
                share_token_4 VARCHAR(100) UNIQUE,
                token_used BOOLEAN DEFAULT 0,
                token_2_used BOOLEAN DEFAULT 0,
                token_3_used BOOLEAN DEFAULT 0,
                token_4_used BOOLEAN DEFAULT 0,
                user_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        '''))
        
        # Копируем данные из старой таблицы
        db.session.execute(text('''
            INSERT INTO photo_new (
                id, filename, original_filename, share_token, 
                share_token_2, share_token_3, share_token_4, user_id
            )
            SELECT id, filename, original_filename, share_token, 
                   share_token_2, share_token_3, share_token_4, user_id 
            FROM photo
        '''))
        
        # Удаляем старую таблицу и переименовываем новую
        db.session.execute(text('DROP TABLE photo'))
        db.session.execute(text('ALTER TABLE photo_new RENAME TO photo'))
        
        # Восстанавливаем связи
        db.session.execute(text('PRAGMA foreign_keys=OFF'))
        db.session.execute(text('UPDATE photo_view SET photo_id = photo_id'))
        db.session.execute(text('PRAGMA foreign_keys=ON'))
        
        db.session.commit()
        print("Миграция для добавления полей использования токенов успешно выполнена")
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        db.session.rollback()
    
    print("Миграция базы данных завершена")
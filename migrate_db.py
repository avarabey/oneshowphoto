from app import app, db
import uuid
from sqlalchemy import text
import sqlalchemy.exc

with app.app_context():
    # Для SQLite нужно использовать другой подход - создать новую таблицу
    try:
        # 1. Создаем временную таблицу с новой структурой
        db.session.execute(text('''
            CREATE TABLE photo_new (
                id INTEGER PRIMARY KEY,
                filename VARCHAR(200) NOT NULL,
                original_filename VARCHAR(200) NOT NULL,
                share_token VARCHAR(100) UNIQUE,
                share_token_2 VARCHAR(100) UNIQUE,
                share_token_3 VARCHAR(100) UNIQUE,
                share_token_4 VARCHAR(100) UNIQUE,
                user_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        '''))
        
        # 2. Копируем данные из старой таблицы, добавляя новые токены
        rows = db.session.execute(text('SELECT id, filename, original_filename, share_token, user_id FROM photo')).fetchall()
        for row in rows:
            db.session.execute(text('''
                INSERT INTO photo_new (id, filename, original_filename, share_token, share_token_2, share_token_3, share_token_4, user_id)
                VALUES (:id, :filename, :original_filename, :share_token, :token2, :token3, :token4, :user_id)
            '''), {
                'id': row[0],
                'filename': row[1],
                'original_filename': row[2],
                'share_token': row[3],
                'token2': str(uuid.uuid4()),
                'token3': str(uuid.uuid4()),
                'token4': str(uuid.uuid4()),
                'user_id': row[4]
            })
        
        # 3. Удаляем старую таблицу и переименовываем новую
        db.session.execute(text('DROP TABLE photo'))
        db.session.execute(text('ALTER TABLE photo_new RENAME TO photo'))
        
        # 4. Восстанавливаем связи с таблицей photo_view
        db.session.execute(text('PRAGMA foreign_keys=OFF'))
        db.session.execute(text('UPDATE photo_view SET photo_id = photo_id'))
        db.session.execute(text('PRAGMA foreign_keys=ON'))
        
        db.session.commit()
        print("Миграция таблицы photo успешно выполнена")
    except Exception as e:
        print(f"Ошибка при миграции таблицы: {e}")
        db.session.rollback()
    
    print("Миграция базы данных завершена")
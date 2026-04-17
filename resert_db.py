from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.book import Book
from app.models.chat import Chat

app = create_app()
with app.app_context():
    # Удаляем все таблицы
    db.drop_all()
    # Создаём заново
    db.create_all()
    print("таблицы созданы:")
    print(db.engine.table_names())
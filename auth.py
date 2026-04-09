from flask import Blueprint, request, jsonify
from flask_login import login_user
import bcrypt
from data import session
from data.models import User

# Создаём Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/register', methods=['POST'])
def api_register():
    data = request.get_json()
    db = session.get_db()

    # Проверка на существование
    existing = db.query(User).filter(
        (User.username == data.get('username')) |
        (User.email == data.get('email'))
    ).first()

    if existing:
        return jsonify({'error': 'Пользователь уже существует'}), 400

    # Хеш
    hashed = bcrypt.hashpw(
        data['password'].encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    # Создание пользователя
    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed
    )

    db.add(user)
    db.commit()

    return jsonify({'message': 'Регистрация успешна'}), 201


@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
    db = session.get_db()

    # Поиск по username ИЛИ email
    user = db.query(User).filter(
        (User.username == data.get('username_or_email')) |
        (User.email == data.get('username_or_email'))
    ).first()

    if user and user.verify_password(data.get('password', '')):
        login_user(user, remember=data.get('remember', False))
        return jsonify({'message': 'Вход выполнен', 'username': user.username}), 200

    return jsonify({'error': 'Неверные данные'}), 401

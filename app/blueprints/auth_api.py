from flask import Blueprint, request, render_template, redirect, url_for, session
from app.services.auth_service import AuthService  # импорт сервиса
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not all([username, email, password, confirm_password]):
        return render_template('register.html', error='Все поля обязательны')

    if password != confirm_password:
        return render_template('register.html', error='Пароли не совпадают')

    try:
        user = AuthService.register_user(username, email, password)
        return redirect(url_for('auth.login'))
    except ValueError as e:
        return render_template('register.html', error=str(e))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Получаем данные из формы
    username = request.form.get('username')
    password = request.form.get('password')

    # Валидация
    if not all([username, password]):
        return render_template('login.html', error='Логин и пароль обязательны')

    try:
        user = AuthService.login_user(username, password)
        # Сохраняем пользователя в сессии
        session['user_id'] = user.id
        # Перенаправляем куда нужно (например, на главную или чат)
        return redirect(url_for('auth.index'))
    except ValueError as e:
        logger.error(f"Ошибка входа: {str(e)}")
        return render_template('login.html', error='Неверный логин или пароль')
    except Exception as e:
        logger.error(f"Неожиданная ошибка при входе: {str(e)}")
        return render_template('login.html', error='Внутренняя ошибка сервера')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))
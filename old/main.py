from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import Api
import bcrypt
from old.data import session
from old.data.models import User, create_tables
from api.auth import api_bp


app = Flask(__name__)
app.register_blueprint(api_bp)
app.config['SECRET_KEY'] = 'secret'
api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    db = session.get_db()
    return db.get(User, int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return f'Привет, {current_user.username}!'
    return send_from_directory('static', 'index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Валидация
        if not username or not email or not password:
            flash('Все поля обязательны для заполнения', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))

        db = session.get_db()

        # Проверка существования
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash('Пользователь с таким именем или email уже существует', 'error')
            return redirect(url_for('register'))

        #Хеш
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.add(new_user)
        db.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        if not username_or_email or not password:
            flash('Все поля обязательны для заполнения', 'error')
            return redirect(url_for('login'))

        db = session.get_db()

        # Поиск по username , email
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and user.verify_password(password):
            login_user(user, remember=remember)
            flash(f'Добро пожаловать, {user.username}!', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя/email или пароль', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)

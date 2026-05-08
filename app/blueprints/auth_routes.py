from flask import Blueprint, render_template, redirect, request
from flask_login import login_user, logout_user
from app.forms.login_form import LoginForm
from app.forms.register_form import RegisterForm
from app.services import AuthService
from logging import getLogger

logger = getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='aslr')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', form=form)
    if form.validate_on_submit():
        try:
            user = AuthService.login_user(form.username.data, form.password.data)
        except ValueError as e:
            logger.error(e)
            return render_template('login.html', form=form, error=e)
        login_user(user)
        return redirect('/chat')
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'GET':
        return render_template('register.html', form=form)
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        conf_password = form.conf_password.data
        if password != conf_password:
            return render_template('register.html',
                                   form=form, error="Пароли не совпадают")
        try:
            user = AuthService.register_user(username, email, password)
        except ValueError as e:
            logger.error(e)
            return render_template('register.html',form=form, error=e)
        login_user(user)
        return redirect('/chat')
    e = form.errors
    return render_template('register.html', form=form, error=e)
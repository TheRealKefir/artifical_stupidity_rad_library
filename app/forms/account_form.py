from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField


class AccountSettings(FlaskForm):
    username = StringField('Введите имя')
    email = EmailField('Введите почту')
    password = PasswordField('Введите пароль')
    submit = SubmitField('Сохранить')

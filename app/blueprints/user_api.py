from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.services.user_service import UserService
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/users', template_folder='../templates')


@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Профиль текущего пользователя"""
    try:
        return render_template('profile.html', user=current_user)
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {str(e)}")
        return render_template('profile.html', error='Не удалось загрузить профиль')


@user_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """Обновление профиля"""
    username = request.form.get('username')
    email = request.form.get('email')

    try:
        if username:
            UserService.update_username(current_user.id, username)
        if email:
            UserService.update_email(current_user.id, email)

        return redirect(url_for('user.get_profile'))
    except ValueError as e:
        logger.error(f"Ошибка обновления: {str(e)}")
        return render_template('profile.html', user=current_user, error=str(e))
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        return render_template('profile.html', user=current_user, error='Внутренняя ошибка')


@user_bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Просмотр профиля другого пользователя"""
    try:
        user = UserService.get_user_by_id(user_id)
        return render_template('user_profile.html', user=user)
    except Exception as e:
        logger.error(f"Ошибка получения пользователя {user_id}: {str(e)}")
        return render_template('user_profile.html', error='Пользователь не найден')
from flask import Blueprint, request, jsonify, g
from app.services.user_service import UserService
from app.decorators.ownership import check_ownership
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api/users')


@user_bp.route('/<int:user_id>', methods=['GET'])
@check_ownership('user')
def get_user(user_id):
    """Получение информации о пользователе"""
    try:
        user = {
            'id': user_id,
            'username': f'user_{user_id}',
            'email': f'user{user_id}@example.com'
        }

        return jsonify({'user': user}), 200
    except Exception as e:
        logger.error(f"Ошибка получения пользователя {user_id}: {str(e)}")
        return jsonify({'error': 'User not found'}), 404


@user_bp.route('/<int:user_id>', methods=['PUT'])
@check_ownership('user')
def update_user(user_id):
    """Обновление информации о пользователе"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        user = None
        #username если передан
        if 'username' in data:
            user = UserService.update_username(user_id, data['username'])

        # email если передан
        if 'email' in data:
            user = UserService.update_email(user_id, data['email'])

        # пароль если передан
        if 'password' in data:
            user = UserService.update_password(user_id, data['password'])

        if not user:
            return jsonify({'error': 'No valid fields to update'}), 400

        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200
    except ValueError as e:
        logger.error(f"Ошибка валидации при обновлении пользователя {user_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@user_bp.route('/<int:user_id>/chats', methods=['GET'])
@check_ownership('user')
def get_user_chats(user_id):
    """Получение списка чатов пользователя"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        chats = [
            {'id': 1, 'title': 'Chat 1', 'created_at': '2026-05-01'},
            {'id': 2, 'title': 'Chat 2', 'created_at': '2026-12-22'}
        ]

        return jsonify({
            'chats': chats,
            'page': page,
            'per_page': per_page,
            'total': len(chats)
        }), 200
    except Exception as e:
        logger.error(f"Ошибка получения чатов пользователя {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """Получение профиля текущего авторизованного пользователя"""
    try:
        current_user = {'id': 1, 'username': 'current_user', 'email': 'user@example.com'}

        return jsonify({'profile': current_user}), 200
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {str(e)}")
        return jsonify({'error': 'Unauthorized'}), 401

@user_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Обновление профиля текущего авторизованного пользователя"""

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    current_user_id = 1

    user = None
    if 'username' in data:
        user = UserService.update_username(current_user_id, data['username'])

    if 'email' in data:
        user = UserService.update_email(current_user_id, data['email'])

    if 'password' in data:
        user = UserService.update_password(current_user_id, data['password'])

    if not user:
        return jsonify({'error': 'No valid fields to update'}), 400

    return jsonify({
        'message': 'Profile updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200
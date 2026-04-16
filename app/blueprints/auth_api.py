from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

# Создаем blueprint для аутентификации
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'error'}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({'error': 'validation'}), 400

        # Регистрация
        user = AuthService.register_user(username, email, password)



    except ValueError as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Неожиданная ошибка при регистрации: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    вход
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username')
        password = data.get('password')

        if not all([username, password]):
            return jsonify({'error': 'Username and password are required'}), 400

        # Аутентификация через AuthService
        user = AuthService.login_user(username, password)

        return jsonify({
            'message': 'Login good',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200

    except ValueError as e:
        logger.error(f"Ошибка входа: {str(e)}")
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Неожиданная ошибка при входе: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:

        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        logger.error(f"Ошибка при выходе: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


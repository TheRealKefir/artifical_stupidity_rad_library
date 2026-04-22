from flask import Blueprint, render_template
from app.extensions import login_manager
from app.services import UserService

root_bp = Blueprint('root_bp', __name__)


@login_manager.user_loader
def load_user(user_id):
    return UserService.get_user_by_id(user_id)


@root_bp.route('/')
def index():
    return render_template('index.html')

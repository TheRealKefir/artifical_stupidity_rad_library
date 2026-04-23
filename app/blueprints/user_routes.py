from flask import Blueprint, request, render_template, redirect
from app.services.user_service import UserService
from app.utils.decorators import check_ownership
from flask_login import login_required, logout_user, current_user
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)


@user_bp.route('/<int:user_id>', methods=['GET'])
@check_ownership
def get_user():
    return UserService.get_user_by_id(current_user.id)


@check_ownership
@user_bp.route("/settings")
@login_required
def settings():
    user = UserService.get_user_by_id(current_user.id)
    return render_template("settings.html", user=user)


@check_ownership
@user_bp.route("/settings/update", methods=["POST"])
@login_required
def settings_update():
    new_username = request.form.get("username")
    new_email = request.form.get("email")
    new_password = request.form.get("password")

    UserService.update_username(current_user.id, new_username)
    UserService.update_email(current_user.id, new_email)
    UserService.update_password(current_user.id, new_password)

    user = UserService.get_user_by_id(current_user.id)
    return render_template("account.html", user=user)


@check_ownership
@user_bp.route("/settings/delete", methods=["POST"])
@login_required
def delete_account():
    UserService.delete_user(current_user.id)
    logout_user()
    return redirect("/register")

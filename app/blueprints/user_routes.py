from flask import Blueprint, render_template, redirect
from flask_login import login_required, logout_user, current_user
from app.utils.helpers import get_password_hash
from app.forms.account_form import AccountSettings
from app.services.user_service import UserService

user_bp = Blueprint('user', __name__, url_prefix='aslr')


@user_bp.route("/settings", methods=["GET"])
@login_required
def settings():
    form = AccountSettings()
    user = UserService.get_user_by_id(current_user.id)
    return render_template("settings.html", user=user, form=form)


@user_bp.route("/settings", methods=["POST"])
@login_required
def settings_update():
    form = AccountSettings()
    user = UserService.get_user_by_id(current_user.id)

    if form.validate_on_submit():
        new_username = form.username.data
        new_password = form.password.data
        new_email = form.email.data

    UserService.update_user(current_user.id, new_username, new_password, new_email)
    user = UserService.get_user_by_id(current_user.id)
    return render_template("settings.html", form=form, user=user)



@user_bp.route("/settings", methods=["DELETE"])
@login_required
def delete_account():
    UserService.delete_user(current_user.id)
    logout_user()
    return redirect("/register")

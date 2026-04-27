from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.chat_service import ChatService
from app.utils.decorators import check_ownership
from app.models import Chat

chat_bp = Blueprint('chat', __name__)


@chat_bp.route("/chat")
@login_required
def chat():
    chats = ChatService.get_user_chats(current_user.id)
    last_chat_id = chats[-1].id - 1 if chats else None
    return render_template("chat.html", chats=chats, last_chat_id=last_chat_id)


@chat_bp.route("/chat/list")
@login_required
def chat_list():
    chats = ChatService.get_user_chats(current_user.id)
    return render_template("partials/chat_list.html", chats=chats)


@chat_bp.route("/chat/create", methods=["POST"])
@login_required
def create_chat():
    new_chat = ChatService.create_chat(current_user.id)
    return render_template(
        "partials/chat_item.html", chat=new_chat, active=True)


@check_ownership(Chat)
@chat_bp.route("/chat/<int:chat_id>/delete", methods=["POST"])
@login_required
def delete_chat(chat_id):
    ChatService.delete_chat(chat_id)
    return "", 204


@chat_bp.route("/chat/<int:chat_id>")
@login_required
@check_ownership(Chat)
def chat_page(chat_id):
    return render_template("chat.html", chat_id=chat_id)


@chat_bp.route("/chat/<int:chat_id>/messages", endpoint="get_messages")
@login_required
@check_ownership(Chat)
def get_messages(chat_id):
    messages = ChatService.get_chat_messages(chat_id)
    return render_template("partials/messages.html", messages=messages)

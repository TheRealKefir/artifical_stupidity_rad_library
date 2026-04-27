from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from torch.distributed.elastic.multiprocessing.redirects import redirect

from app.services.chat_service import ChatService
from app.utils.decorators import check_ownership
from app.forms.book_form import BookForm
import os
from app.tasks import process_book_task

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


@check_ownership
@chat_bp.route("/chat/<int:chat_id>/delete", methods=["POST"])
@login_required
def delete_chat(chat_id):
    ChatService.delete_chat(chat_id)
    return redirect('/chat')


@check_ownership
@chat_bp.route("/chat/<int:chat_id>")
@login_required
def open_chat(chat_id):
    messages = ChatService.get_chat_messages(chat_id)
    return render_template("partials/messages.html", messages=messages)


@chat_bp.route('/upload', methods='POST')
@login_required
def upload_book():
    form = BookForm()
    if form.validate_on_submit():
        file = form.book.data
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        os.makedirs(current_app.config, exist_ok=True)
        file.save(file_path)

        process_book_task.delay(
            file_path=file_path,
            user_id=current_user.id,
        )

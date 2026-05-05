from flask import Blueprint, render_template, current_app, redirect, request

from flask_login import login_required, current_user

from app.services.chat_service import ChatService
from app.utils.decorators import check_ownership
from app.forms.book_form import BookForm
import os
from app.tasks import process_book_task
from app.models import Chat
from app.services import AIService, RagService

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


@chat_bp.route("/chat/<int:chat_id>/delete", methods=["POST"])
@login_required
@check_ownership(Chat, id_arg='chat_id')
def delete_chat(chat_id):
    ChatService.delete_chat(chat_id)
    return redirect('/chat')


@chat_bp.route("/chat/<int:chat_id>", methods=['GET'])
@login_required
@check_ownership(Chat, id_arg='chat_id')
def open_chat(chat_id):
    chats = ChatService.get_user_chats(current_user.id)
    return render_template("chat.html", chats=chats, chat_id=chat_id)


@chat_bp.route("/chat/<int:chat_id>/messages")
@login_required
@check_ownership(Chat, id_arg='chat_id')
def get_messages(chat_id):
    messages = ChatService.get_chat_messages(chat_id)
    return render_template("partials/messages.html", messages=messages)


@chat_bp.route('/upload', methods=['POST'])
@login_required
def upload_book():
    form = BookForm()
    if form.validate_on_submit():
        file = form.book.data
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        process_book_task.delay(
            file_path=file_path,
            user_id=current_user.id
        )
        return redirect('/chat')

    return render_template('upload_book.html', form=form), 400


@chat_bp.route('/upload', methods=['GET'])
@login_required
def get_upload_book():
    form = BookForm()
    return render_template('upload_book.html', form=form)


@chat_bp.route("/send/<int:chat_id>", methods=["POST"])
@login_required
def send_message(chat_id):
    content = request.form.get("text")
    if not content: return "", 204

    user_msg = ChatService.save_message(chat_id, current_user.id, "user", content)
    return render_template("partials/message.html", msg=user_msg, trigger_ai=True)


@chat_bp.route("/generate/<int:chat_id>", methods=["POST"])
@login_required
def generate_ai_answer(chat_id):
    bot_msg = ChatService.process_ai_response(chat_id, current_user.id)
    return render_template("partials/message.html", msg=bot_msg)

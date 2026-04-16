from app import create_app
from flask import render_template, request
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

# временное хранилище
messages_store = {
    1: [
        {"role": "bot", "text": "Привет, я твой AI"},
    ]
}


@app.route("/messages/<int:chat_id>")
def get_messages(chat_id):
    messages = messages_store.get(chat_id, [])
    return render_template("partials/messages.html", messages=messages)


@app.route("/send/<int:chat_id>", methods=["POST"])
def send(chat_id):
    text = request.form["text"]

    user_msg = {"role": "user", "text": text}
    messages_store.setdefault(chat_id, []).append(user_msg)

    # фейковый ответ
    bot_msg = {"role": "bot", "text": f"Ответ на: {text}"}
    messages_store[chat_id].append(bot_msg)

    return render_template(
        "partials/messages.html",
        messages=[user_msg, bot_msg]
    )


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)

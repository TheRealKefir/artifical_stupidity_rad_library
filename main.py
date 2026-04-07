from flask import Flask
from flask_login import LoginManager
from flask_restful import Api
from data import session
from data.models import User, create_tables


app = Flask(__name__)
api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db = session.get_db()
    return db.get(User, user_id)

@app.route('/', methods=['GET'])
def index():
    return 'Hello, World!'


if __name__ == '__main__':
    create_tables()

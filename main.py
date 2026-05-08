from app import create_app
from flask import render_template, request
from config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == "__main__":
    print(app.config)
    app.run(host='127.0.0.1', port=22867, debug=True)

from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms.fields import FileField

class BookForm(FlaskForm):
    book = FileField('Book', validators=[DataRequired()])
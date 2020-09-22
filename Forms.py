from flask_wtf import FlaskForm
from wtforms import SelectField, BooleanField, SubmitField
from wtforms.fields.html5 import DateField


class LoginForm(FlaskForm):
    departName = SelectField(choices=[])
    operDate = DateField('operDate', format='%Y-%m-%d')
    remember = BooleanField("Запомнить", default=False)
    submit = SubmitField("Войти")

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FileField, DateField
from wtforms.validators import DataRequired, URL, Optional

class LogForm(FlaskForm):
    attempt = SelectField('Log your attemot!', choices=[(i, str(i)) for i in range(1, 21)] + [(21, '20+')], coerce=int) # Add "20+" as the last option    
    evaluation = SelectField('Rate the climb!', choices=[(1, '⭐️'), (2, '⭐️ ⭐️'), (3, '⭐️ ⭐️ ⭐️'), (4, '⭐️ ⭐️ ⭐️ ⭐️'), (5, '⭐️ ⭐️ ⭐️ ⭐️ ⭐️')])

    # Need to find a way to allocate different behavior for each submit type
    sent = SubmitField('Sent!')
    not_sent = SubmitField('Not yet')

class AddClimb(FlaskForm):
    img = FileField('Upload an image of the climb', validators=[Optional()])
    style = SelectField('Select the style of the climb', choices=[('Finger', 'Finger'), ('Power', 'Power'), ('Pinch', 'Pinch'), ('Sloper', 'Sloper'), ('Balance', 'Balance'), ('Cordination', 'Cordination'), ('Technical', 'Technical'), ('Endurance', 'Endurance')], validators=[Optional()])
    when_stripped = DateField('When will the climb removed', format='%Y-%m-%d', validators=[Optional()])
    grade = SelectField('Grade', choices=[(i) for i in range(1, 15)], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Upload')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    user_name = StringField('*User Name', validators=[DataRequired()])
    email = StringField('*Email', validators=[DataRequired()])
    password = StringField('*Password', validators=[DataRequired()])
    current_grade = SelectField('*Grade', choices=[(i) for i in range(1, 15)], coerce=int, validators=[DataRequired()])
    user_icon = FileField('Upload an image of the climb', validators=[Optional()])
    home_gym = StringField('Home Gym', validators=[Optional()])

    submit = SubmitField('Register')
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SubmitField, SelectField
from wtforms.validators import InputRequired

class PlayerForm(FlaskForm):

    name = StringField('Name', validators=[InputRequired()])
    age = IntegerField('Age', validators=[InputRequired()])
    height = FloatField('Height (inches)', validators=[InputRequired()])
    team = SelectField('Team', coerce=int)
    position = SelectField('Position', coerce=int)
    submit = SubmitField('Save Player')

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired

class TeamForm(FlaskForm):
    team_name = StringField('Team Name', validators=[InputRequired()])
    submit = SubmitField('Add Team')
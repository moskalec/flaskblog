from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import EmailField, PasswordField, BooleanField, SubmitField, StringField, SelectField
from wtforms.validators import DataRequired, Email, Length, ValidationError, EqualTo

from flaskblog.models import User
from flaskblog.users.utils import locales


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Log in")


class AccountUpdateForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=6, max=20)]
    )
    given_name = StringField("Name")
    family_name = StringField("Family name")
    locale = SelectField("Locale", choices=locales())
    email = EmailField("Email", validators=[DataRequired(), Email()])
    picture = FileField(
        "Update profile picture", validators=[FileAllowed(["jpg", "png"])]
    )
    submit = SubmitField("Update")

    def validate_username(self, field):
        if current_user.username != field.data:
            if User.query.filter_by(username=field.data).first():
                raise ValidationError("User exists")

    def validate_email(self, field):
        if current_user.email != field.data:
            if User.query.filter_by(email=field.data).first():
                raise ValidationError("Email exists")


class RegisterForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=6, max=20)]
    )
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Register")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("User exists")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email exists")


class RequestResetPasswordForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Reset password")

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user is None:
            raise ValidationError("Email does not exists")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Set new Password")

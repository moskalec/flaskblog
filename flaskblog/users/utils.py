import os
import secrets

from PIL import Image
from flask import url_for, current_app
from flask_mail import Message

from flaskblog import login_manager, mail
from flaskblog.models import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def save_profile_image(file_image):
    filename = secrets.token_hex(8)

    image = Image.open(file_image)
    image.thumbnail(size=(125, 125))

    _, file_ext = os.path.splitext(file_image.filename)
    new_filename = filename + file_ext
    image.save(
        os.path.join(current_app.root_path, "static/profile_pics", new_filename),
        optimize=True,
        quality=65,
    )
    return new_filename


def send_reset_mail(user):
    token = user.get_reset_token()
    msg = Message(
        "Password Reset Request", sender="noreply@demo.com", recipients=[user.email]
    )
    msg.body = f"""To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
    """
    mail.send(msg)


def locales():
    return [('en', 'English'), ('ua', 'Ukrainian')]

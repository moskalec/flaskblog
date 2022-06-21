from datetime import datetime

from flask_login import UserMixin
from flask_security import RoleMixin

from flaskblog import db


roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    posts = db.relationship("Post", backref=db.backref("author", lazy=True))
    profile_pic = db.Column(db.String(20))
    image_name = db.Column(db.String(20), default="default.jpg")
    given_name = db.Column(db.String(20))
    family_name = db.Column(db.String(20))
    locale = db.Column(db.String(6))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )

    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = token[-1]
        except:
            return None
        return User.query.get(user_id)

    def get_reset_token(self):
        s = "12345" + str(self.id)
        return s

    def __repr__(self):
        return "<User %r>" % self.username

    def __str__(self):
        return self.username


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return "<Post %r>" % self.title

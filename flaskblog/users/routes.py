import json
from datetime import datetime

import requests
from flask import url_for, redirect, request, flash, render_template, Blueprint
from flask_login import current_user, login_user, login_required, logout_user

from flaskblog import bcrypt, db, Config, client
from flaskblog.models import User
from flaskblog.users.forms import (
    LoginForm,
    RegisterForm,
    AccountUpdateForm,
    RequestResetPasswordForm,
    ResetPasswordForm,
)
from flaskblog.users.utils import save_profile_image, send_reset_mail

users = Blueprint("users", __name__)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("login.html", title="Login", form=form)


def get_google_provider_cfg():
    return requests.get(Config.GOOGLE_DISCOVERY_URL).json()


@users.route("/g_login")
def g_login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@users.route("/g_login/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(Config.GOOGLE_CLIENT_ID, Config.GOOGLE_CLIENT_SECRET),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        users_username = userinfo_response.json()["name"]
        users_given_name = userinfo_response.json()["given_name"]
        users_family_name = userinfo_response.json()["family_name"]
        users_picture = userinfo_response.json()["picture"]
        users_email = userinfo_response.json()["email"]
        users_locale = userinfo_response.json()["locale"]
    else:
        return "User email not available or not verified by Google.", 400

    users_password = bcrypt.generate_password_hash(
        datetime.now().strftime("%f") + Config.SECRET_KEY
    ).decode("utf-8")

    user = User.query.filter_by(email=users_email).first()

    if not user:
        user = User(
            username=users_username,
            given_name=users_given_name,
            family_name=users_family_name,
            email=users_email,
            profile_pic=users_picture,
            password=users_password,
            locale=users_locale,
        )
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for("main.home"))


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You are now able to log in", "success")
        return redirect(url_for("users.login"))
    return render_template("register.html", title="Register", form=form)


@users.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = AccountUpdateForm(obj=current_user)
    image_file = url_for("static", filename="profile_pics/" + current_user.image_name)
    if form.validate_on_submit():
        if form.picture.data:
            current_user.image_name = save_profile_image(form.picture.data)
            db.session.commit()
        current_user.username = form.username.data
        current_user.given_name = form.given_name.data
        current_user.family_name = form.family_name.data
        current_user.locale = form.locale.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated", "success")
        return redirect(url_for("users.account"))
    return render_template(
        "account.html", title="Account", form=form, image_file=image_file
    )


@users.route("/reset_password", methods=["GET", "POST"])
def request_reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_mail(user)
        flash("Check your email", "success")
        return redirect(url_for("main.home"))
    return render_template(
        "request_reset_password.html", title="Reset password", form=form
    )


@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = ResetPasswordForm()
    user = User.verify_reset_token(token)
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user.password = hashed_password
        db.session.commit()
        flash("Your account has been created! You are now able to log in", "success")
        return redirect(url_for("users.login"))
    return render_template("reset_password.html", title="Set new password", form=form)

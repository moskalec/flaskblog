from flask import abort, render_template, flash, redirect, url_for, request, Blueprint
from flask_login import login_required, current_user

from flaskblog import db
from flaskblog.models import Post, User
from flaskblog.posts.forms import CreatePostForm


posts = Blueprint("posts", __name__)


@posts.route("/post/<int:post_id>")
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", title=post.title, post=post)


@posts.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = CreatePostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Post updated", "success")
        return redirect(url_for("main.home"))
    return render_template("create_post.html", legend="Update post", form=form)


@posts.route("/post/<int:post_id>/delete", methods=["GET", "POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post has been deleted", "success")
    return redirect(url_for("main.home"))


@posts.route("/new_post", methods=["GET", "POST"])
@login_required
def new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data, content=form.content.data, author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash("New post created", "success")
        return redirect(url_for("main.home"))
    return render_template("create_post.html", legend="Create post", form=form)


@posts.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = (
        Post.query.filter_by(author=user)
        .order_by(Post.created.desc())
        .paginate(per_page=5, page=page)
    )
    return render_template("user_posts.html", posts=posts, user=user)

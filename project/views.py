"""Blog routes, authentication, and database operations."""

from functools import wraps

import bleach
from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    session,
    flash,
    redirect,
    url_for,
    jsonify,
)

from project.extensions import db
from project.models import Post

bp = Blueprint("blog", __name__)


def login_required(view):
    @wraps(view)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in.")
            return jsonify({"status": 0, "message": "Please log in."}), 401
        return view(*args, **kwargs)

    return decorated_function


@bp.route("/")
def index():
    entries = db.session.scalars(db.select(Post).order_by(Post.id.desc())).all()
    return render_template("index.html", entries=entries)


@bp.route("/add", methods=["POST"])
@login_required
def add_entry():
    title = request.form.get("title", "").strip()
    text = request.form.get("text", "").strip()
    if not title or not text:
        return "Title and text are required.", 400
    # Preserve the tutorial's basic HTML formatting without executing arbitrary HTML.
    text = bleach.clean(
        text,
        tags=["strong", "em", "b", "i", "p", "br", "ul", "ol", "li"],
        attributes={},
        strip=True,
    )
    if not text.strip():
        return "Text must contain content.", 400
    db.session.add(Post(title, text))
    db.session.commit()
    flash("New entry was successfully posted")
    return redirect(url_for("index"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("username") != current_app.config["USERNAME"]:
            error = "Invalid username"
        elif request.form.get("password") != current_app.config["PASSWORD"]:
            error = "Invalid password"
        else:
            session.clear()
            session["logged_in"] = True
            flash("You were logged in")
            return redirect(url_for("index"))
    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    flash("You were logged out")
    return redirect(url_for("index"))


@bp.route("/delete/<int:post_id>", methods=["GET"])
@login_required
def delete_entry(post_id):
    """Keep the tutorial's GET endpoint for this course demonstration."""
    post = db.session.get(Post, post_id)
    if post is None:
        return jsonify({"status": 0, "message": "Post not found."}), 404
    db.session.delete(post)
    db.session.commit()
    flash("The entry was deleted.")
    return jsonify({"status": 1, "message": "Post Deleted"})


@bp.route("/search/")
def search():
    query = request.args.get("query", "").strip()
    entries = []
    if query:
        # Match the tutorial's literal, case-insensitive title-or-body search.
        posts = db.session.scalars(db.select(Post).order_by(Post.id.desc())).all()
        entries = [
            post
            for post in posts
            if query.lower() in post.title.lower() or query.lower() in post.text.lower()
        ]
    return render_template("search.html", entries=entries, query=query)


@bp.route("/health")
def health():
    # Query the application table so a missing schema also fails the health check.
    db.session.execute(db.select(Post.id).limit(1))
    return jsonify({"status": "ok"})

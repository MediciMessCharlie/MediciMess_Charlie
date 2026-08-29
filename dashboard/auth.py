"""Local session authentication for the Phase 7 dashboard."""

import os

from flask import (
    Flask,
    has_request_context,
    redirect,
    render_template_string,
    request,
    session,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .access import Role, UserAccess, can_view_branch, can_view_network


DEMO_PASSWORD = "medici-demo"
DEMO_USERS = {
    "director": (generate_password_hash(DEMO_PASSWORD), Role.MANAGING_DIRECTOR, None),
    "rome.manager": (
        generate_password_hash(DEMO_PASSWORD),
        Role.BRANCH_MANAGER,
        "Rome",
    ),
}

LOGIN_PAGE = """<!doctype html>
<html><head><title>Medici Bank Login</title>
<style>
body{background:#f5f0e8;color:#3e2723;font-family:Georgia,serif;margin:0}
main{background:#fffdf8;border:1px solid #d7c9b5;border-top:5px solid #b8860b;
margin:10vh auto;max-width:420px;padding:2rem}label,input{display:block;width:100%}
label{font-family:Arial,sans-serif;font-weight:bold;margin-top:1rem}
input{box-sizing:border-box;margin-top:.4rem;padding:.7rem}button{background:#8b1a1a;
border:0;color:white;font-weight:bold;margin-top:1.25rem;padding:.8rem;width:100%}
.error{color:#c62828}</style></head><body><main><h1>Medici Bank</h1>
<p>Sign in to the operations dashboard.</p>{% if error %}<p class="error">{{ error }}</p>{% endif %}
<form method="post"><label>Username<input name="username" required></label>
<label>Password<input name="password" type="password" required></label>
<button type="submit">Sign in</button></form></main></body></html>"""


def current_user() -> UserAccess | None:
    """Return the authenticated dashboard user from the signed session."""
    if not has_request_context():
        return None
    username = session.get("username")
    details = DEMO_USERS.get(username)
    if details is None:
        return None
    _password_hash, role, branch = details
    return UserAccess(username, role, branch)


def configure_auth(server: Flask) -> None:
    """Register login, logout, and page authorization on the Dash server."""
    server.secret_key = os.environ.get(
        "MEDICIMESS_SESSION_SECRET", "local-development-secret-change-me"
    )

    @server.route("/login", methods=["GET", "POST"])
    def login():
        error = ""
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            details = DEMO_USERS.get(username)
            if details and check_password_hash(details[0], password):
                session.clear()
                session["username"] = username
                user = current_user()
                destination = "/" if can_view_network(user) else f"/branch/{user.branch}"
                return redirect(destination)
            error = "Invalid username or password."
        return render_template_string(LOGIN_PAGE, error=error)

    @server.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    @server.before_request
    def protect_dashboard_pages():
        if request.path in {"/login", "/logout"} or request.path.startswith(
            "/assets/"
        ):
            return None
        user = current_user()
        if user is None:
            return redirect("/login")
        if request.path == "/" and not can_view_network(user):
            return redirect(f"/branch/{user.branch}")
        if request.path.startswith("/branch/"):
            branch = request.path.removeprefix("/branch/")
            if not can_view_branch(user, branch):
                return redirect(f"/branch/{user.branch}")
        return None

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
<html><head><title>Medici Bank · Sovereign Ledger</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--gold:#d9b15f;--ink:#08090b;--panel:#111318;--muted:#9c9a93;--wine:#651c25}
*{box-sizing:border-box}body{background:radial-gradient(circle at 50% 10%,#28221a 0,
#111216 34%,#07080a 75%);color:#f4ead5;font-family:Georgia,serif;margin:0;min-height:100vh;
display:grid;place-items:center}body:before{content:"";position:fixed;inset:0;pointer-events:none;
background:linear-gradient(rgba(217,177,95,.025) 1px,transparent 1px),
linear-gradient(90deg,rgba(217,177,95,.025) 1px,transparent 1px);background-size:42px 42px}
main{background:linear-gradient(145deg,rgba(24,25,29,.98),rgba(10,11,14,.98));
border:1px solid rgba(217,177,95,.35);box-shadow:0 30px 90px #000,0 0 0 1px #000;
margin:3rem 1rem;max-width:440px;padding:2.5rem;position:relative;width:100%}
main:before{background:linear-gradient(90deg,transparent,var(--gold),transparent);content:"";
height:2px;left:12%;position:absolute;right:12%;top:0}.seal{display:block;filter:drop-shadow(0 8px 16px #000);
height:132px;margin:-.5rem auto .8rem;width:132px;object-fit:contain}.kicker{color:var(--gold);
font:700 .67rem Arial,sans-serif;letter-spacing:.23em;text-align:center;text-transform:uppercase}
h1{font-size:2rem;font-weight:500;letter-spacing:.03em;margin:.45rem 0;text-align:center}
.intro{color:var(--muted);font:400 .88rem Arial,sans-serif;line-height:1.6;text-align:center}
label,input{display:block;width:100%}label{color:#d8d4ca;font:700 .7rem Arial,sans-serif;
letter-spacing:.12em;margin-top:1.25rem;text-transform:uppercase}input{background:#090a0d;border:1px solid #34363c;
color:#fff;margin-top:.5rem;outline:0;padding:.85rem}input:focus{border-color:var(--gold);
box-shadow:0 0 0 3px rgba(217,177,95,.1)}button{background:linear-gradient(135deg,#7a2530,var(--wine));
border:1px solid #a95860;color:white;cursor:pointer;font:700 .72rem Arial,sans-serif;
letter-spacing:.16em;margin-top:1.5rem;padding:.95rem;width:100%;text-transform:uppercase}
button:hover{filter:brightness(1.15)}.error{color:#ff8c91;font:700 .8rem Arial,sans-serif;text-align:center}
.foot{color:#6f706f;font:400 .67rem Arial,sans-serif;letter-spacing:.08em;margin:1.4rem 0 0;
text-align:center;text-transform:uppercase}.theme{background:transparent;border:1px solid rgba(217,177,95,.5);
border-radius:999px;color:var(--gold);font:700 .62rem Arial,sans-serif;letter-spacing:.09em;
margin:0;min-width:120px;padding:.55rem;position:fixed;right:1rem;top:1rem;width:auto}
html.light body{background:radial-gradient(circle at 50% 10%,#fff7e7 0,#ece6da 55%,#ddd4c5 100%);
color:#241d18}html.light main{background:linear-gradient(145deg,#fff,#f6f0e5);border-color:#b99756;
box-shadow:0 25px 70px rgba(62,39,20,.18)}html.light .intro{color:#6f685e}html.light input{background:#fff;
border-color:#c9bdab;color:#241d18}html.light label{color:#514a42}html.light .foot{color:#777067}
</style></head><body><button class="theme" id="theme-switch" type="button">Florentine Day</button><main>
<img class="seal" src="/assets/medici-bank-seal.png" alt="Medici Bank seal">
<div class="kicker">The Sovereign Ledger</div><h1>Medici Bank</h1>
<p class="intro">Enter the private intelligence network for branch operations and treasury oversight.</p>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
<form method="post"><label>Username<input name="username" required></label>
<label>Password<input name="password" type="password" required></label>
<button type="submit">Enter the ledger</button></form><p class="foot">Florence · Roma · Venezia · The Medici Network</p>
</main><script>
const root=document.documentElement,control=document.getElementById('theme-switch');
function applyTheme(theme){const light=theme==='light';root.classList.toggle('light',light);
control.textContent=light?'Sicilian Night':'Florentine Day';control.setAttribute('aria-label',
light?'Switch to dark mode':'Switch to light mode');localStorage.setItem('medicimess-theme',theme)}
applyTheme(localStorage.getItem('medicimess-theme')||'dark');
control.addEventListener('click',()=>applyTheme(root.classList.contains('light')?'dark':'light'));
</script></body></html>"""


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

import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
#db = SQL("sqlite:///events.db")

uri = os.getenv("\
postgres://ncuysuvnkairwl:c766c379dcb5d6b1a85263033beea27c3792ec7e0d249ba4c6d0cdca39bc4c97@ec2-54-194-211-183.eu-west-1.compute.amazonaws.com:5432/dht5er8aa5tuh\
")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
#    """Hello"""

    return render_template("index.html")


@app.route("/need", methods=["GET", "POST"])
@login_required
def need():
    """Общий список потребностей"""
    if request.method == "GET":
        need_db = db.execute("SELECT ENU.category, ENU.description, users.username FROM \
                            (SELECT need.*, event_need_user.* FROM need \
                             INNER JOIN event_need_user ON need.id = event_need_user.need_id) ENU \
                             LEFT JOIN users ON users.id = ENU.user_id ORDER BY ENU.category;")
        return render_template("need.html", need=need_db)
    else:
        user_id = session["user_id"]
        category = request.form.get("category")
        description = request.form.get("description")
        need_id_db = db.execute("SELECT id FROM need WHERE category=? AND description=?", category, description)

        db.execute("UPDATE event_need_user SET user_id=? WHERE event_id=1 AND need_id=?;", user_id, need_id_db[0]["id"])

        return redirect("/need")


@app.route("/add_need", methods=["GET", "POST"])
@login_required
def add_need():
    """Общий список потребностей"""
    if request.method == "GET":
        return render_template("add_need.html")
    else:
        category = request.form.get("category")
        description = request.form.get("description")

        db.execute("INSERT INTO need(category, description) VALUES (?, ?)",
                category, description)
        need_id_db = db.execute("SELECT id FROM need WHERE category=? AND description=?", category, description)

        db.execute("INSERT INTO event_need_user(event_id, need_id) VALUES (1, ?)", need_id_db[0]["id"])
        return redirect("/need")


@app.route("/participant")
@login_required
def participant():
    """Список участников мероприятия"""
    users_db = db.execute("SELECT DISTINCT username, mob_phone, email FROM users INNER JOIN event_user ON users.id = event_user.user_id")
    return render_template("participant.html", users=users_db)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        email = request.form.get("email")
        mob_phone = request.form.get("mob_phone")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username")

        if not password:
            return apology("must provide password")

        if not confirmation:
            return apology("must provide confirmation")

        if password != confirmation:
            return apology("passord and confirmation do not match")

        hash = generate_password_hash(password)

        try:
            new_user = db.execute("INSERT INTO users(username, hash, email, mob_phone) VALUES (?, ?, ?, ?)", username, hash, email, mob_phone)
        except:
            return apology("username already registered")

        session["user_id"] = new_user

        return redirect("/")


@app.route("/my_task", methods=["GET", "POST"])
@login_required
def my_task():
    """Sell shares of stock"""
    if request.method == "GET":
        user_id = session["user_id"]
        task_user_db = db.execute(
            "SELECT ENU.category, ENU.description FROM \
                            (SELECT need.*, event_need_user.* FROM need \
                             INNER JOIN event_need_user ON need.id = event_need_user.need_id) ENU \
                             LEFT JOIN users ON users.id = ENU.user_id WHERE users.id=?;", user_id)
        return render_template("my_task.html", task_user=task_user_db)



@app.route("/photo")
@login_required
def photo():
    return render_template("photos.html")


@app.route("/event", methods=["GET", "POST"])
@login_required
def event():
    """Ближайшее мероприятие"""
    if request.method == "GET":
        return render_template("event.html")
    else:
        user_id = session["user_id"]
        event_id_db = db.execute("SELECT id FROM event WHERE name_event ='Лесной поход'")
        event_id = event_id_db[0]["id"]
        db.execute("INSERT INTO event_user (event_id, user_id) VALUES (?, ?)",
            event_id, user_id)
        return redirect("/need")

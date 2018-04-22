from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import sqlite3
import datetime

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")

conn = sqlite3.connect('finance.db')
conn.row_factory = sqlite3.Row
db = conn.cursor()


@app.route("/")
@login_required
def index():
    session_id = session["user_id"]

    db.execute("SELECT *, SUM(qty) FROM users JOIN history ON users.id = history.id WHERE users.id = :id GROUP BY stock", 
        (session_id,))
    stocks = db.fetchall()

    db.execute("SELECT symbol FROM users JOIN history ON users.id = history.id WHERE users.id = :id AND history.type = :buy GROUP BY stock", 
        (session_id, 'BUY'))
    symbols = db.fetchall()

    db.execute("SELECT cash FROM users WHERE id = :id", (session_id,))
    cash = db.fetchone()
    
    current_price = []
    
    for symbol in symbols:
        quote = lookup(str(symbol['symbol']))
        current_price.append(quote['price'])

    return render_template("index.html", stocks = stocks, current_price = current_price, cash = cash)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""

    if request.method == "POST":
        stock = lookup(request.form.get("stock symbol"))
        stock_name = stock["name"]
        stock_qty = int(request.form.get("qty"))
        stocks_price = float(stock["price"])*stock_qty
        session_id = session["user_id"]
        db.execute("SELECT cash FROM users WHERE id = :id", (session_id,))
        cash = (db.fetchone())[0]

        if cash < stocks_price:
            return apology("You don't have enough money")
        else:
            new_cash = cash - stocks_price
            db.execute("UPDATE users SET cash = :cash WHERE id = :id", (new_cash, session_id))
            db.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?, ?, ?)", (session_id, stock_name, str(datetime.datetime.now()), stock_qty, 
                request.form.get("stock symbol"), float(stock['price']), 'BUY'))
            conn.commit()
            return redirect(url_for("index"))
    else:
        return render_template("display.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""

    session_id = session["user_id"]
    db.execute("SELECT * FROM history WHERE history.id = :id", (session_id,))
    history = db.fetchall()

    return render_template("history.html", history = history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = :username", (username,))

        # ensure username exists and password is correct
        results = rows.fetchone()
        if results is None or not pwd_context.verify(request.form.get("password"), results[2]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = results[0]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        stock = lookup(request.form.get("stock symbol"))
        return render_template("quoted.html", name = stock["name"], price = stock["price"], symbol = stock["symbol"])

    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must enter username")

        elif not request.form.get("password") or not request.form.get("Repeat Password"):
            return apology("must enter password")

        elif request.form.get("password") != request.form.get("Repeat Password"):
            return apology("passwords must match")

        # Hash the given password
        hash = pwd_context.encrypt(request.form.get("password"))

        # Register the user in the database
        username = request.form.get("username")
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", (username, hash) )
        conn.commit()

        if not result:
            return apology("username already taken")

        # Log in automatically
        #session["user_id"]

        return redirect(url_for("index"))
    
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "POST":
        stock = lookup(request.form.get("stock symbol"))
        stock_name = stock["name"]
        stock_qty = -1*int(request.form.get("qty"))
        stocks_price = float(stock["price"])*stock_qty
        session_id = session["user_id"]

        # Updates user cash
        db.execute("SELECT cash FROM users WHERE id = :id", (session_id,))
        current_cash = db.fetchone()
        new_cash = current_cash['cash'] + abs(stock_qty*float(stock["price"]))
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", (new_cash, session_id))

        db.execute("SELECT *, SUM(qty) FROM users JOIN history ON users.id = history.id WHERE users.id = :id AND history.type = :buy AND history.stock = :stock GROUP BY stock", 
            (session_id, 'BUY', stock_name))
        stocks = db.fetchone() # or fetchall(), let's test
        
        current_stocks = int(stocks[11])

        if abs(stock_qty) > current_stocks:
            return apology("You don't own that many stocks!")

        db.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?, ?, ?)", (session_id, stock_name, str(datetime.datetime.now()), stock_qty,
            request.form.get("stock symbol"), float(stock['price']), 'SELL'))
        conn.commit()

        return redirect(url_for("index"))

    else:
        return render_template("sell.html")



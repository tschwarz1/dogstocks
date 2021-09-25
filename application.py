import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/",  methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    #stock, symbol, unit price, quantity, value
    print("entered index")
    userid = session["user_id"]
    cash = db.execute('SELECT cash FROM users WHERE id=(?)', userid)
    holdings = db.execute("SELECT stock_name, stock_quantity FROM holdings WHERE user_id=(?) AND stock_quantity>(?)", userid, 0)
    data = [] #stock, symbol, unit price, quantity, value
    for count, item in enumerate(holdings):
        current = lookup(item['stock_name'])
        data.append([])
        data[count].append(current['name'])
        data[count].append(current['symbol'])
        data[count].append(current['price'])
        data[count].append(item['stock_quantity'])
        value = (item['stock_quantity']) * (current['price'])
        data[count].append(value)
    empty = False;
    if len(data) == 0:
        empty = True;
    return render_template("index.html", data=data, empty=empty, cash=cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        quantity = request.form.get("quantity")
        stock = request.form.get("stock")
        price = lookup(request.form.get("stock"))
        value = (price['price']) * float(quantity)
        userid = session["user_id"]

        user = db.execute("SELECT username FROM users WHERE id=(?)", userid)
        cash = db.execute("SELECT cash FROM users WHERE id=(?)", userid)
        cash = cash[0]['cash']
        if value > cash:
            return apology("insufficient cash", 403)
        
        if not quantity or not stock:
            return apology("bad data entry at buy POST", 403)

        existing = db.execute("SELECT stock_name from holdings where \
                                user_id=(?) AND stock_name=(?)", \
                                userid, price['symbol'])

        if existing:#add to exisiting holding
            current = db.execute("SELECT stock_quantity FROM holdings WHERE \
                                user_id=(?) AND stock_name=(?)", \
                                userid, price['symbol'])
            print(current)
            new_quantity = (current[0]['stock_quantity']) + int(quantity)
            print("ALREADY EXISTS")
            db.execute("UPDATE holdings SET stock_quantity=(?) \
                        WHERE user_id=(?) AND stock_name=(?)", new_quantity, userid, price['symbol'])

        else:#create new holding
            print("NEW STOCK FOR THIS USER")
            db.execute("INSERT INTO holdings(user_id, stock_name, stock_quantity) \
                    VALUES ((?), (?), (?))", userid, price['symbol'], quantity)

        #ADD TO TRANSACTIONS
        value = float(quantity) * price['price']
        db.execute("INSERT INTO transactions (transaction_time, user_id, quantity, stock, unit_price, value) \
                    VALUES (CURRENT_TIMESTAMP, (?),(?),(?),(?),(?) )",
                    userid, quantity, price['symbol'], price['price'], value)
                    
        #subtract from cash
        db.execute("UPDATE users set cash=(?) where id=(?)", (cash-value), userid)



        return render_template("bought.html", quantity=quantity, stock=stock, price=price, value=value, user=user)
    else:
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    userid = session["user_id"]
    transactions = db.execute("SELECT transaction_id, transaction_time, stock, unit_price, quantity, value FROM transactions WHERE user_id=(?)", userid)
    print(transactions)
    data = [] #stock, symbol, unit price, quantity, value
    x = 'transaction_time'
    for count, item in enumerate(transactions):
        data.append([])
        data[count].append(item['transaction_id'])
        data[count].append(item[x])
        data[count].append(item['stock'])
        data[count].append(item['unit_price'])
        data[count].append(item['quantity'])
        data[count].append(item['value'])

    return render_template("history.html", data=data)


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        quote = lookup(request.form.get("quote"))
        print(quote)
        return render_template("quoted.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        existingun = db.execute("SELECT username FROM users")

        name = request.form.get("username")
        password = request.form.get("password")
        passwordconf = request.form.get("passwordconf")

        #check input is good
        if not name or not password or not passwordconf:
            return apology("input missing", 403)
        if password != passwordconf:
            return apology("passwords do not match", 403)
        for row in existingun:
            if name in row['username']:
                return apology("Username already exists", 403)

        hashed = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        db.execute("INSERT INTO users (username, hash) VALUES ((?), (?))", name, hashed)
        return redirect("/")

    if request.method == "GET":
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    userid = session["user_id"]
    options = db.execute("SELECT stock_name FROM holdings WHERE user_id=(?)", userid)

    if request.method == "POST":
        quantity = int(request.form.get("quantity"))
        quantity = -quantity
        stock = lookup(request.form.get("symbol"))
        value = (stock['price']) * float(quantity)
        print('quantity, stock ', quantity, stock)
        cash = db.execute("SELECT cash FROM users WHERE id=(?)", userid)
        cash = cash[0]['cash']

        current = db.execute("SELECT stock_quantity FROM holdings WHERE \
                                 user_id=(?) AND stock_name=(?)",
                                 userid, stock['symbol'])

        if -quantity > (current[0]['stock_quantity']):
            return apology("you don't have that many", 403)

        new_quantity = (current[0]['stock_quantity']) + (quantity)
        db.execute("UPDATE holdings SET stock_quantity=(?) \
                    WHERE user_id=(?) AND stock_name=(?)", new_quantity, userid, stock['symbol'])

        #Add to transactions
        db.execute("INSERT INTO transactions (transaction_time, user_id, quantity, stock, unit_price, value) \
                     VALUES (CURRENT_TIMESTAMP, (?),(?),(?),(?),(?) )",
                     userid, quantity, stock['symbol'], stock['price'], value)
                     
        db.execute("UPDATE users set cash=(?) where id=(?)", (cash-value), userid)

        return redirect("/")
        #return render_template("bought.html", quantity=quantity, stock=stock, price=price, value=value, user=user)
    else:
        return render_template("sell.html", options=options)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

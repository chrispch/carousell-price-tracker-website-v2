from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from functools import wraps
from itsdangerous import BadSignature
from werkzeug.debug import DebuggedApplication
import sys, os
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
os.chdir(abspath)
from analytics import price_statistics, graph
from database import *
from scrapper import *
from send_email import send_confirmation
from confirmation_tokens import generate_confirmation_token, confirm_token


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://price-tracker-v2:pricetracker@localhost/price-tracker-v2'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:hern3010@localhost/price-tracker-v2'
app.config['SECURITY_PASSWORD_SALT'] = "cant_guess_this"
app.config['LOG_FILE'] = '/var/log/price_tracker/application.log'
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
db = SQLAlchemy(app)
application = DebuggedApplication(app, True)

urls_file = "urls.csv"
preview_content = None
categories = list(load_links(urls_file).keys())
categories.sort()


# Decorators
def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session["logged_in"]:
            return func(*args, **kwargs)
        else:
            flash("Requested page is only accessible after logging in.")
            return redirect(url_for("home"))
    return decorated_function


def redirect_get(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if request.method == "GET":
            return redirect(url_for("home"))
        else:
            return func(*args, **kwargs)
    return decorated_function


# View
@app.route('/')
def home():
    return render_template("home.html", database_nav="nav-link",
                                   trackers_nav="nav-link")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if db.session.query(User).filter(User.email == email).count() == 0:
            flash("Email is not registered. Please register before logging in.")
            return redirect(url_for("home"))
        elif not db.session.query(User).filter(User.email == email).first().confirmed:
            flash("Please confirm your email and try again.")
            return redirect(url_for("home"))
        else:
            encrypted_password = db.session.query(User.password).filter(User.email == email).first()[0]
            if sha256_crypt.verify(password, encrypted_password):
                session["logged_in"] = True
                session["user_email"] = email
                return redirect(url_for("home"))
            else:
                flash("Password is incorrect. Please try again.")
                return redirect(url_for("home"))


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        email = request.form["email"]
        password = sha256_crypt.encrypt(request.form["password"])
        # if account exists but not yet confirmed, recreate account and send confirmation email
        if db.session.query(User).filter(User.email == email).count() != 0:
            if not db.session.query(User).filter(User.email == email).first().confirmed:
                # delete user
                db.session.delete(db.session.query(User).filter(User.email == email).first())
                db.session.commit()
                # create user
                if create_user(email, password):
                    # generate token and confirm url
                    token = generate_confirmation_token(email, app.config["SECRET_KEY"], app.config["SECURITY_PASSWORD_SALT"])
                    confirm_url = url_for("confirm_email", token=token, _external=True)
                    # generate html template
                    html_template = render_template("confirm_email_template.html", confirm_url=confirm_url)
                    # send confirmation email
                    send_confirmation(email, html_template)
                    # print("recreating account")
                    flash("Please check your email for confirmation.")
                    return redirect(url_for("home"))
            else:
                flash("Email is already in use, please try again.")
                return redirect(url_for("home"))
        # create account if it does not exist
        elif db.session.query(User).filter(User.email == email).count() == 0:
            print("account does not exist")
            # create user
            if create_user(email, password):
                print("User created")
                # generate token and confirm url
                token = generate_confirmation_token(email, app.config["SECRET_KEY"], app.config["SECURITY_PASSWORD_SALT"])
                confirm_url = url_for("confirm_email", token=token, _external=True)
                # generate html template
                html_template = render_template("confirm_email_template.html", confirm_url=confirm_url)
                # send confirmation email
                send_confirmation(email, html_template)
                flash("Please check your email for confirmation.")
                return redirect(url_for("home"))
            else:
                print("Email in use")
                flash("Email is already in use, please try again.")
                return redirect(url_for("home"))
        else:
            flash("Account is already created")
            return redirect(url_for("home"))


@app.route('/logout', methods=["GET", "POST"])
def logout():
    session['logged_in'] = False
    session['user_email'] = None
    return redirect(url_for("home"))


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token, app.config["SECRET_KEY"], app.config["SECURITY_PASSWORD_SALT"])
        # if email already confirmed
        if db.session.query(User).filter(User.email == email).first().confirmed:
            flash('Account already confirmed. Please login.', 'success')
            return redirect(url_for("home"))
        else:
            # update session variables
            session["user_email"] = email
            session['logged_in'] = True
            # update database
            db.session.query(User).filter(User.email == email).first().confirmed = True
            db.session.commit()
            return redirect(url_for("home"))

    except BadSignature:
        flash('The confirmation link is invalid or has expired. Try creating a new account.', 'danger')


@app.route('/trackers', methods=["GET", "POST"])
@login_required
def trackers():
    try:
        trackers = db.session.query(Tracker).filter(Tracker.user_email == session["user_email"]).all()
        if request.method == "POST":
            # get form input (from add tab)
            current_category = request.form["category"]
            current_name = request.form["name"]
            current_search = request.form["search"]
            alert_price = request.form["alert_price"]
            alert_percentage = request.form["alert_percentage"]
            if not alert_price and not alert_percentage:
                flash("Please enter either an alert price or percentage (or both)")
                return redirect(url_for("trackers"))

            # handle preview content (for add tab) from database
            global preview_content
            # url = urls[current_category]
            # preview_content = scrap(url)
            # preview_content = filter_data(preview_content, exception_words, exception_words, price_range)
            preview_content = db.session.query(Data).filter(Data.category == current_category).all()
            # apply search terms
            if current_search != "":
                preview_content = search_data(preview_content, current_search)
            # return price stats
            if preview_content:
                price_stats = price_statistics(preview_content)
            else:
                price_stats = None

            return render_template("trackers.html", categories=categories,
                                   current_category=current_category,
                                   current_name=current_name, current_search=current_search,
                                   alert_price=alert_price, alert_percentage=alert_percentage,
                                   database_nav="nav-link", trackers_nav="nav-link active",
                                   preview_content=preview_content,
                                   trackers=trackers, price_stats=price_stats)
        elif request.method == "GET":
                # on first loading trackers.html
                global preview_content
                preview_content = None
                return render_template("trackers.html", categories=categories, current_category=categories[0],
                                       name="", url="", database_nav="nav-link",
                                       trackers_nav="nav-link active", preview_content=preview_content,
                                       price_stats=None, trackers=trackers, alert_price=0, alert_percentage=0)



    except Exception as e:
        return render_template("error.html", error=e)


@app.route('/database', methods=["GET", "POST"])
@login_required
def database():
    try:
        if request.method == "POST":
            # get form input
            current_category = request.form["category"]
            current_search = request.form["search"]
            # get data from selected category
            data = list(db.session.query(Data).filter(Data.category == current_category).all())
            # search data based on form input
            data = search_data(data, current_search)
            # get price statistics and graph
            if data:
                price_stats = price_statistics(data)
                graph(data)

                return render_template("database.html", database_nav="nav-link active", trackers_nav="nav-link",
                                       current_search=current_search, data=data, current_category=current_category,
                                       price_stats=price_stats, categories=categories)
            # if no data to return
            else:
                return render_template("database.html", database_nav="nav-link active", trackers_nav="nav-link",
                                       current_search=current_search, data=None, price_stats=None, categories=categories)
        elif request.method == "GET":
            return render_template("database.html", database_nav="nav-link active", trackers_nav="nav-link",
                                   categories=categories, data=None, price_stats=None)

    except Exception as e:
        return render_template("error.html", error=e)


@app.route('/add', methods=["GET", "POST"])
@redirect_get
def add():
    current_user = session["user_email"]
    # get form input (from add tab)
    current_category = request.form["category"]
    current_name = request.form["name"]
    current_search = request.form["search"]
    alert_price = request.form["alert_price"]
    alert_percentage = request.form["alert_percentage"]
    if not alert_price and not alert_percentage:
        flash("Please enter either an alert price or percentage (or both)")
        return redirect(url_for("trackers"))
    if create_tracker(current_name, current_user, current_category, current_search, float(alert_price), float(alert_percentage)):
        flash("Tracker '{}' added successfully!".format(current_name))
    else:
        flash("Tracker name is already in use. Please try again.")
    return redirect(url_for("trackers"))


@app.route('/del_tracker', methods=["GET", "POST"])
@redirect_get
def del_tracker():
    delete_tracker(request.form["delete"])
    flash("Tracker '{}' deleted successfully!".format(request.form["delete"]))
    return redirect(url_for("trackers"))


@app.route('/rename_tracker', methods=["GET", "POST"])
@redirect_get
def rename_tracker():
    old_name = request.form["rename"]
    new_name = request.form["name"]
    if db.session.query(Tracker).filter(Tracker.name == new_name).count() == 0:
        db.session.query(Tracker).filter(Tracker.name == old_name).first().name = new_name
        db.session.commit()
        flash("{} renamed to {} successfully".format(old_name, new_name))
        return redirect(url_for("trackers"))
    else:
        flash("Tracker name already in use. Rename failed.")
        return redirect(url_for("trackers"))


@app.route('/del_data', methods=["GET", "POST"])
@redirect_get
def del_data():
    delete_data(int(request.form["delete"]))
    return redirect(url_for("database"))


# to run on local host
if __name__ == "__main__":
    app.debug = True
    # category = "Electronics"
    # data = scrap("https://carousell.com/categories/electronics-7/?sort_by=time_created%2Cdescending&collection_id=7&cc_id=361")
    # data = filter_data(data, exception_words, exception_words, price_range)
    # for d in data:
    #     create_data(d["name"], d["price"], d["date"], d["link"], category)
    app.run()

else:
    # to run on apache server
    pass

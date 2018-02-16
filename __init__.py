from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask_apscheduler import APScheduler
from passlib.hash import sha256_crypt
from analytics import price_statistics, graph
from database import create_tracker, create_user, delete_tracker, delete_data, scrap_into_database
from scrapper import scrap, filter_data, search_data, exception_words, price_range

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:hern3010@localhost/price-tracker'
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
db = SQLAlchemy(app)
preview_content = None
categories = []
categories_to_crawl = ["Electronics"]
urls_to_crawl = {}


class Config(object):
    JOBS = [
        {
            'id': 'scrap_into_database',
            'func': 'database:scrap_into_database',
            'args': 'urls_to_crawl',
            'trigger': 'interval',
            'seconds': 60
        },
        {
            'id': 'price_alert',
            'func': 'database:price_alert',
            'trigger': 'interval',
            'seconds': 60
        }
    ]


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
        if create_user(email, password):
            session['logged_in'] = True
            session["user_email"] = email
            return redirect(url_for("home"))
        else:
            flash("Email is already in use, please try again.")
            return redirect(url_for("home"))


@app.route('/logout', methods=["GET", "POST"])
def logout():
    session['logged_in'] = False
    session['user_email'] = None
    return redirect(url_for("home"))


@app.route('/trackers', methods=["GET", "POST"])
def trackers():
    try:
        if session["logged_in"]:
            # get user's trackers (for manage tab)
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
                # handle preview content (for add tab)
                global preview_content
                url = urls_to_crawl[current_category]
                preview_content = scrap(url)
                preview_content = filter_data(preview_content, exception_words, exception_words, price_range)
                preview_content = search_data(preview_content, current_search)
                return render_template("trackers.html", categories=categories,
                                       current_category=current_category,
                                       current_name=current_name, current_search=current_search,
                                       alert_price=alert_price, alert_percentage=alert_percentage,
                                       database_nav="nav-link", trackers_nav="nav-link active",
                                       preview_content=preview_content,
                                       trackers=trackers)
            elif request.method == "GET":
                    # on first loading trackers.html
                    global preview_content
                    preview_content = None
                    return render_template("trackers.html", categories=categories, current_category=categories[0],
                                           name="", url="", database_nav="nav-link",
                                           trackers_nav="nav-link active", preview_content=preview_content,
                                           trackers=trackers)


    except:
        flash("Requested page is only accessible after logging in.")
        return redirect(url_for("home"))


@app.route('/database', methods=["GET", "POST"])
def database():
    try:
        if session["logged_in"]:
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
                                           current_search=current_search, data=data, price_stats=price_stats, categories=categories)
                # if no data to return
                else:
                    return render_template("database.html", database_nav="nav-link active", trackers_nav="nav-link",
                                           current_search=current_search, data=None, price_stats=None, categories=categories)
            elif request.method == "GET":
                return render_template("database.html", database_nav="nav-link active", trackers_nav="nav-link",
                                       categories=categories)
        else:
                return redirect(url_for("home"))

    except Exception as e:
        return render_template("error.html", error=e)
        # flash("Requested page is only accessible after logging in.")
        # return redirect(url_for("home"))


@app.route('/add', methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
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
        if create_tracker(current_name, current_user, current_category, current_search, alert_price, alert_percentage):
            flash("Tracker '{}' added successfully!".format(current_name))
            url = urls_to_crawl[current_category]
            scrap_into_database(url)
        else:
            flash("Tracker name is already in use. Please try again.")
        return redirect(url_for("trackers"))


@app.route('/del_tracker', methods=["GET", "POST"])
def del_tracker():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        delete_tracker(request.form["delete"])
        flash("Tracker '{}' deleted successfully!".format(request.form["delete"]))
        return redirect(url_for("trackers"))


@app.route('/rename_tracker', methods=["GET", "POST"])
def rename_tracker():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        old_name = request.form["rename"]
        new_name = request.form["name"]
        if db.session.query(Tracker).filter(Tracker.name == new_name).count() == 0:
            db.session.query(Tracker).filter(Tracker.name == old_name).first().name = new_name
            db.session.commit()
            flash("Tracker renamed successfully")
            return redirect(url_for("trackers"))
        else:
            flash("Tracker name already in use. Rename failed.")
            return redirect(url_for("trackers"))


@app.route('/del_data', methods=["GET", "POST"])
def del_data():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        delete_data(int(request.form["delete"]))
        return redirect(url_for("database"))


if __name__ == "__main__":
    app.debug = True
    # get all urls
    urls = get_links()
    global urls_to_crawl
    global categories
    for k in urls:
        # get urls to scrap
        if k in categories_to_crawl:
            # get keys from urls as category lists
            categories.append(k)
            urls_to_crawl[k] = urls[k]

    # schedule scrapper
    app.config.from_object(Config())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run()

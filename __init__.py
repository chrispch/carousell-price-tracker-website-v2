from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask_apscheduler import APScheduler
from passlib.hash import sha256_crypt
from analytics import price_statistics, graph
from database import *
from scrapper import *

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
            # get user's trackers
            trackers = db.session.query(Tracker).filter(Tracker.user_email == session["user_email"]).all()
            for tracker in trackers:
                tracker_info = {}
                tracker_info["name"] = tracker.name
                tracker_info["category"] = tracker.category
                tracker_info["subcategory"] = tracker.subcategory
                tracker_info["url"] = tracker.url
                tracker_info["active"] = tracker.active

            if request.method == "POST":
                current_category = request.form["category"]
                current_name = request.form["name"]
                # current_url = request.form["url"]
                global preview_content
                preview_content = None
                return render_template("trackers.html", categories=categories,
                                       current_category=current_category,
                                       name=current_name, database_nav="nav-link",
                                       trackers_nav="nav-link active",
                                       preview_content=preview_content)

            elif request.method == "GET":
                    # on first loading trackers.html
                    global preview_content
                    preview_content = None
                    return render_template("trackers.html", categories=categories, subcategories=subcategories["Electronics"],
                                           current_category="Electronics", name="", url="", database_nav="nav-link",
                                           trackers_nav="nav-link active", active_trackers=active_trackers,
                                           inactive_trackers=inactive_trackers, preview_content=preview_content)


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
        current_name = request.form["name"]
        # current_url = request.form["url"]
        # if current_url is not "":
        #     current_category = "-"
        #     current_subcategory = "-"
        # else:
        current_url = ""
        current_category = request.form["category"]
        current_subcategory = request.form["subcategory"]
        current_user = session["user_email"]
        if create_tracker(current_user, current_name, current_category, current_subcategory, current_url, True):
            flash("Tracker '{}' added successfully!".format(current_name))
            scrap_into_database()
        else:
            flash("Tracker name is already in use. Please try again.")
        return redirect(url_for("trackers"))


@app.route('/preview', methods=["GET", "POST"])
def preview():
    # get user's trackers
    active_trackers = []
    inactive_trackers = []
    user_id = db.session.query(User.user_id).filter(User.email == session["user_email"]).first()
    tracker_ids = db.session.query(UsersToTrackers.tracker_id).filter(UsersToTrackers.user_id == user_id).all()
    for tracker_id in tracker_ids:
        tracker = db.session.query(Tracker).filter(Tracker.tracker_id == tracker_id).first()
        tracker_info = {}
        tracker_info["name"] = tracker.name
        tracker_info["category"] = tracker.category
        tracker_info["subcategory"] = tracker.subcategory
        tracker_info["url"] = tracker.url
        tracker_info["active"] = tracker.active
        # active trackers
        if tracker_info["active"]:
            active_trackers.append(tracker_info)
        else:
            inactive_trackers.append(tracker_info)

    if request.method == "POST":
        current_category = request.form["category"]
        current_subcategory = request.form["subcategory"]
        current_name = request.form["name"]
        # current_url = request.form["url"]
        # global categories, subcategories
        # if not current_url:
        #     current_url = categories[current_category] + subcategories[current_category][current_subcategory]
        current_url = categories[current_category] + subcategories[current_category][current_subcategory] + "?sort_by=time_created%2Cdescending"
        global preview_content
        preview_content = scrap(current_url)
        return render_template("trackers.html", categories=categories,
                               subcategories=subcategories[current_category],
                               current_category=current_category,
                               name=current_name, url=current_url, database_nav="nav-link",
                               trackers_nav="nav-link active", active_trackers=active_trackers,
                               inactive_trackers=inactive_trackers, preview_content=preview_content,
                               current_url=current_url)

    elif request.method == "GET":
        return redirect(url_for("home"))


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


@app.route('/info_tracker', methods=["GET", "POST"])
def info_tracker():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        return redirect(url_for("database"))


@app.route('/start_tracker', methods=["GET", "POST"])
def start_tracker():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        db.session.query(Tracker).filter(Tracker.name == request.form["start"]).first().active = True
        db.session.commit()
        flash("Tracker '{}' started successfully!".format(request.form["start"]))
        return redirect(url_for("trackers"))


@app.route('/stop_tracker', methods=["GET", "POST"])
def stop_tracker():
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        db.session.query(Tracker).filter(Tracker.name == request.form["stop"]).first().active = False
        db.session.commit()
        flash("Tracker '{}' stopped successfully!".format(request.form["stop"]))
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
        # get keys from urls as category lists
        categories.append(k)
        # get urls to scrap
        if k in categories_to_crawl:
            urls_to_crawl[k] = urls[k]

    # schedule scrapper
    app.config.from_object(Config())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run()

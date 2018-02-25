# from sqlalchemy import create_engine, db.Column, db.Integer, db.Float, db.String, MetaData, Table
# from sqlalchemy.orm import sessionmaker, mapper
# from sqlalchemy.ext.declarative import declarative_base
# from flask_sqlalchemy import SQLAlchemy

from __init__ import db, app
from scrapper import search_data
from analytics import price_statistics
from send_email import send_alert
from flask import render_template


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    confirmed = db.Column(db.Boolean)

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.confirmed = False


class Tracker(db.Model):
    __tablename__ = "trackers"
    tracker_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    user_email = db.Column(db.String)
    category = db.Column(db.String)
    search = db.Column(db.String)
    alert_price = db.Column(db.Float)
    alert_percentage = db.Column(db.Float)
    ave_price = db.Column(db.Float)
    tracked_items = db.Column(db.Integer)

    def __init__(self, name, user_email, category, search, alert_price, alert_percentage, ave_price, tracked_items):
        self.name = name
        self.user_email = user_email
        self.category = category
        self.search = search
        self.alert_price = alert_price
        self.alert_percentage = alert_percentage
        self.ave_price = ave_price
        self.tracked_items = tracked_items


class Data(db.Model):
    __tablename__ = "data"
    data_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Float)
    date = db.Column(db.String)
    link = db.Column(db.String)
    category = db.Column(db.String)

    def __init__(self, name, price, date, link, category):
        self.name = name
        self.price = price
        self.date = date
        self.link = link
        self.category = category


def create_user(email, password):
    new_user = User(email=email, password=password)
    if db.session.query(User).filter(User.email == new_user.email).count() == 0:
        db.session.add(new_user)
        db.session.commit()
        return True


def create_tracker(name, user, category, search, alert_price, alert_percentage):
    # create and add tracker
    if db.session.query(Tracker).filter(Tracker.name == name).count() == 0:
        # get average price of all current data entries corresponding to tracker
        data = db.session.query(Data).filter(
            Data.category == category).all()
        results = search_data(data, search)
        if results:
            ave_price = price_statistics(results)["ave_price"]
            # get number of data entries corresponding to tracker (to calculate future averages)
            tracked_items = len(results)
        else:
            ave_price = 0
            tracked_items = 0
        # add tracker
        new_tracker = Tracker(name, user, category, search,
                              alert_price, alert_percentage,
                              ave_price, tracked_items)
        db.session.add(new_tracker)
        db.session.commit()
        return True


def create_data(name, price, date, link, category):
    new_data = Data(name, price, date, link, category)
    query_data = db.session.query(Data).filter(Data.name == new_data.name). \
        filter(Data.date == new_data.date). \
        filter(Data.price == new_data.price)
    # if listing of same name, price and date not already in database, add data to database
    if query_data.count() == 0:
        db.session.add(new_data)
        price_alert(new_data)
        db.session.commit()
    # if same listing has multiple categories, add new category to data
    elif category not in query_data.first().category.split(", "):
        print("multiple categories!")
        to_append = ", " + category
        query_data.first().category += to_append
        db.session.commit()


def delete_tracker(tracker_name):
    print(tracker_name)
    trackerid = db.session.query(Tracker.tracker_id).filter(
        Tracker.name == tracker_name).first()
    if trackerid:  # if tracker exists
        tracker = db.session.query(Tracker).get(trackerid)
        db.session.delete(tracker)
        db.session.commit()


def delete_data(data_id):
    data = db.session.query(Data).get(data_id)
    db.session.delete(data)
    db.session.commit()


def delete_all_data():
    for i in db.session.query(Data).all():
        db.session.delete(i)
        db.session.commit()


def price_alert(listing):
    # get trackers
    trackers = db.session.query(Tracker).all()
    for tracker in trackers:
        # if listing is tracked by tracker
        tracked_words = set(tracker.search.lower().split(" "))
        if bool(set(listing.name.lower().split(" ")).intersection(tracked_words)):
            print("this is tracked:", listing.name)
            # if listing price triggers price alert
            if listing.price <= tracker.alert_price or listing.price <= tracker.ave_price * tracker.alert_percentage:
                # generate and send price alert email
                with app.app_context():
                    html_template = render_template("price_alert_email_template.html", listing=listing, tracker=tracker)
                to_email = str(tracker.user_email)
                send_alert(to_email, html_template)
                print("Data alert: ", listing.link)
                # update tracker ave_price and tracked items
                tracker.tracked_items = int(tracker.tracked_items) + 1
                tracker.ave_price = (tracker.ave_price + listing.price)/tracker.tracked_items
                db.session.commit()


db.create_all()


# create_user(email="test1@mail.com", password="pw")
# create_tracker(user="test1@mail.com", name="h2", category="Electronics", subcategory="Audio", url="", status="activated")
# create_data("h2", "test_data", 5.0, "5/5/18")

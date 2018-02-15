# from sqlalchemy import create_engine, db.Column, db.Integer, db.Float, db.String, MetaData, Table
# from sqlalchemy.orm import sessionmaker, mapper
# from sqlalchemy.ext.declarative import declarative_base
# from flask_sqlalchemy import SQLAlchemy

from __init__ import db
from scrapper import scrap, filter_data, exception_words, price_range, search_data
from analytics import price_statistics


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)

    def __init__(self, email, password):
        self.email = email
        self.password = password


class Tracker(db.Model):
    __tablename__ = "trackers"
    tracker_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    user_email = db.Column(db.String)
    category = db.Column(db.String)
    search = db.Column(db.String)
    alert_price = db.Column(db.Float)
    alert_percentage = db.Column(db.Float)

    def __init__(self, name, user_email, category, search):
        self.name = name
        self.user_email = user_email
        self.category = category
        self.search = search


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
    new_tracker = Tracker(name, user, category, search, alert_price, alert_percentage)
    db.session.add(new_tracker)
    db.session.commit()


def create_data(name, price, date, link, category):
    new_data = Data(name, price, date, link, category)
    # if listing of same name, price and date not already in database, add data to database
    if db.session.query(Data).filter(Data.name == new_data.name).\
                              filter(Data.date == new_data.date).\
                              filter(Data.price == new_data.price).count() == 0:
        db.session.add(new_data)
        db.session.commit()


def delete_tracker(tracker_name):
    print(tracker_name)
    trackerid = db.session.query(Tracker.tracker_id).filter(Tracker.name == tracker_name).first()
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


def scrap_into_database(urls):
    print("Scrapping into database")
    # saves crawled data in database
    for category, url in urls.items():
        data = scrap(url)
        data = filter_data(data, exception_words, exception_words, price_range)
        for d in data:
            create_data(d["name"], d["price"], d["date"], d["link"], category)


def price_alert():
    # get trackers
    trackers = db.session.query(Tracker).all()
    for tracker in trackers:
        data = db.session.query(Data).filter(Data.category == tracker.category).all()
        results = search_data(data, tracker.search)
        ave_price = price_statistics(results)["ave_price"]
        for d in data:
            if d.price <= tracker.alert_price\
             or d.price <= ave_price * tracker.alert_percentage:
                print("Data alert: ", d.link)

# TODO: change database location to refer to new table


db.create_all()
# delete_all_data()


# create_user(email="test1@mail.com", password="pw")
# create_tracker(user="test1@mail.com", name="h2", category="Electronics", subcategory="Audio", url="", status="activated")
# create_data("h2", "test_data", 5.0, "5/5/18")

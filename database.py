# from sqlalchemy import create_engine, db.Column, db.Integer, db.Float, db.String, MetaData, Table
# from sqlalchemy.orm import sessionmaker, mapper
# from sqlalchemy.ext.declarative import declarative_base
# from flask_sqlalchemy import SQLAlchemy

from __init__ import db
from scrapper import scrap

# global categories, subcategories
categories = {"Electronics": "https://carousell.com/categories/electronics-7/",
              "Mobiles & Tablets": "https://carousell.com/categories/mobile-phones-215/"}

subcategories = {"Electronics": {"All": "",
                                 "Computers": "computers-tablets-213/",
                                 "TV & Entertainment Systems": "tvs-entertainment-systems-217/",
                                 "Audio": "audio-207/",
                                 "Computer Parts & Accessories": "computer-parts-accessories-214/",
                                 "Others": "electronics-others-218/"},
                 "Mobiles & Tablets": {"All": "",
                                       "iPhones": "iphones-1235/",
                                       "Android": "androidphones-1237/"}}


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


def create_tracker(user, name, category, subcategory, url, status):
    if url:
        effective_url = url
    else:
        effective_url = categories[category] + subcategories[category][subcategory] + "?sort_by=time_created%2Cdescending"
    # create and add tracker
    new_tracker = Tracker(name, category, subcategory, effective_url, status)
    if db.session.query(Tracker).filter(Tracker.name == new_tracker.name).count() == 0:
        print("Tracker added")
        db.session.add(new_tracker)
        db.session.commit()

        # create and add relation to user
        userid = db.session.query(User.user_id).filter(User.email == user).first()
        trackerid = db.session.query(Tracker.tracker_id).filter(Tracker.name == name).first()
        new_relation = UsersToTrackers(userid, trackerid)
        if db.session.query(UsersToTrackers).filter(UsersToTrackers.tracker_id == trackerid).count() == 0:
            db.session.add(new_relation)
            db.session.commit()
        return True
    else:
        return False


def create_data(tracker, name, price, date, link):
    new_data = Data(name=name, price=price, date=date, link=link)
    # if listing of same name, price and date not already in database, add data to database
    if db.session.query(Data).filter(Data.name == new_data.name).\
                              filter(Data.date == new_data.date).\
                              filter(Data.price == new_data.price).count() == 0:
        db.session.add(new_data)
        db.session.commit()
        dataid = new_data.data_id
    else:
        # print(new_data.name, new_data.price, new_data.date)
        dataid = db.session.query(Data.data_id).filter(Data.name == new_data.name).\
                                                        filter(Data.date == new_data.date).\
                                                        filter(Data.price == new_data.price).first()
        # print(dataid)

    trackerid = db.session.query(Tracker.tracker_id).filter(Tracker.name == tracker).first()
    # if tracker-data relation does not yet exist, add relation
    if trackerid not in db.session.query(TrackersToData.tracker_id).filter(TrackersToData.data_id == dataid).all():
        new_relation = TrackersToData(trackerid, dataid)
        db.session.add(new_relation)
        db.session.commit()


def delete_tracker(tracker_name):
    print(tracker_name)
    trackerid = db.session.query(Tracker.tracker_id).filter(Tracker.name == tracker_name).first()
    if trackerid:  # if tracker exists
        tracker = db.session.query(Tracker).get(trackerid)
        tracker_relation = db.session.query(UsersToTrackers).get(trackerid)
        db.session.delete(tracker)
        db.session.delete(tracker_relation)
        db.session.commit()

    # delete associated data and relation object
    related_data = []
    for relation_object in db.session.query(TrackersToData).filter(TrackersToData.tracker_id == trackerid).all():
        related_data.append(relation_object.data_id)
        db.session.delete(relation_object)
        db.session.commit()
    for data in db.session.query(Data).filter(Data.data_id.in_(related_data)).all():
        db.session.delete(data)
        db.session.commit()


def delete_data(data_id):
    # trackerid = db.session.query(Tracker.tracker_id).filter(Tracker.name == tracker_name).first()
    # if data_id:  # if tracker exists
    # dataid = db.session.query(Data.data_id).filter(Data.data_id == data_id).first()
    data = db.session.query(Data).get(data_id)
    data_relation = db.session.query(TrackersToData).filter(TrackersToData.data_id == data_id).first()
    db.session.delete(data)
    db.session.delete(data_relation)
    db.session.commit()


def delete_all_data():
    for i in db.session.query(Data).all():
        db.session.delete(i)
        db.session.commit()
    for i in db.session.query(TrackersToData).all():
        db.session.delete(i)
        db.session.commit()


def scrap_into_database():
    print("Scrapping into database")
    trackers = db.session.query(Tracker).all()
    for c in trackers:
        data = scrap(c.url)
        for d in data:
            create_data(c.name, d["name"], d["price"], d["date"], d["link"])


db.create_all()
# delete_all_data()


# create_user(email="test1@mail.com", password="pw")
# create_tracker(user="test1@mail.com", name="h2", category="Electronics", subcategory="Audio", url="", status="activated")
# create_data("h2", "test_data", 5.0, "5/5/18")

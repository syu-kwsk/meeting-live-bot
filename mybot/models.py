from mybot import db
from flask_sqlalchemy import SQLAlchemy


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Text)
    time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return "<Group id={} time={}>".format(self.group_id, self.time)


def init():
    db.create_all()


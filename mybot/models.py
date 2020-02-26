from mybot import db
from flask_sqlalchemy import SQLAlchemy


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Text)
    time = db.Column(db.DateTime, nullable=True)
    users = db.relationship('User', backref='room', lazy=True)
    def __repr__(self):
        return "<Group id={} time={}>".format(self.group_id, self.time)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text)
    name = db.Column(db.Integer)
    rank = db.Column(db.Integer, nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    def __repr__(self):
        return "<userId={} groupId={} name={} rank={}>".format(self.user_id, self.room_id, self.name, self.rank)

def init():
    db.create_all()


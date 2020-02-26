import os

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "sqlite:///room.db"
SQLALCHEMY_TRACK_MODIFICATIONS = True
SECRET_KEY="secret key"


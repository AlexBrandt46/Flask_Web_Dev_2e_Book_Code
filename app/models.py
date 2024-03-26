""" Module contains each of the different models used to represent objects in the database """

from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from . import loginManager
from flask import current_app
import jwt
from datetime import datetime, timezone, timedelta

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        secret_key = current_app.config['SECRET_KEY']
        encoded = jwt.encode({'confirm': self.id,
                              'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=7200)},
                             secret_key)

        return encoded

    def confirm(self, token):
        secret_key = current_app.config['SECRET_KEY']

        try:
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)
        return True

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

@loginManager.user_loader
def load_user(user_id: str) -> User:
    """ Function required by Flask-Login to be invoked when the extension needs to load
    a user from the database given its identifier

    Args:
        user_id (string): id of the user to retrieve info for

    Returns:
        User: User model containing data associated with user_id
    """
    return User.query.get(int(user_id))

""" Module contains each of the different models used to represent objects in the database """

import hashlib
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app
import jwt
from app import db
from . import loginManager

class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.column(db.String(32))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
                
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

    def __repr__(self):
        return f'<User {self.username}>'

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
                              'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=expiration)},
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

    def generate_reset_token(self, expiration=3600):
        secret_key = current_app.config['SECRET_KEY']
        encoded = jwt.encode({'reset': self.id,
                              'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=expiration)},
                             secret_key)
        return encoded
    
    @staticmethod
    def reset_password(token, new_password):
        secret_key = current_app.config['SECRET_KEY']
        try:
            data = jwt.decode(token, secret_key)
        except:
            False
            
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        secret_key = current_app.config['SECRET_KEY']
        encoded = jwt.encode({'change_email': self.id, 'new_email': new_email,
                              'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=expiration)},
                             secret_key)
        
    def change_email(self, token):
        secret_key = current_app.config['SECRET_KEY']
        try:
            data = jwt.decode(token, secret_key)
        except:
            return False
        
        if data.get('change_email') != self.id:
            return False
        
        new_email = data.get('new_email')
        if new_email is None:
            return False
        
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    def can(self, perm) -> bool:
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self) -> bool:
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating
        )

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

loginManager.anonymous_user = AnonymousUser

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def __repr__(self):
        return '<Role %r>' % self.name

    def add_permission(self, perm: Permission):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm) -> bool:
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                          Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                              Permission.MODERATE, Permission.ADMIN]
        }

        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()

            if role is None:
                role = Role(name=r)

            role.reset_permissions()

            for perm in roles[r]:
                role.add_permission(perm)

            role.default = (role.name == default_role)
            db.session.add(role)

        db.session.commit()

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


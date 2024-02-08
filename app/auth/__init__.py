""" Initializer for Authentication Blueprint """

from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views
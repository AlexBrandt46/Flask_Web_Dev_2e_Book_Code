from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from app import app

bootstrap = Bootstrap(app)

@app.route('/')
def index() -> str:
    """ View function that returns contents to display in "/" route

    Returns:
        str: A string containing the contents of the "/" route
    """
    return render_template('index.html')

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

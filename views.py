from app import app

@app.route('/')
def index() -> str:
    """ View function that returns contents to display in "/" route

    Returns:
        str: A string containing the contents of the "/" route
    """
    return '<h1>Hello World!</h1>'

@app.route('/user/<name>')
def user(name):
    return '<h1>Hello, {}!</h1>'.format(name)

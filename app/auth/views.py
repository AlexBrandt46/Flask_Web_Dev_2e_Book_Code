""" Authentication Blueprint Routes and View Functions """

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm
from app import db
from ..email import send_email

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')

            if next is None or not next.startswith('/'):
                next = url_for('main.index')

            return redirect(next)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """ User registration route which adds new users to the database.
        Before redirecting, the route will send a confirmation email.
        Handles GET and POST requests. """
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create a new User object with the data provided in the form and add it to the database
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()

        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user,
                   token=token)

        flash('A confirmation email has been sent to you via email.')

        return redirect(url_for('auth.login'))

    # Return user to registration page if validation of their input fails
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token: int):
    """
    Route that users are redirected to after confirming their account from the email sent by `/register`.
    It first checks that the logged-in user is already confirmed will redirect them to the home page if they are.
    If not validated, then `confirm()` is called, and a message will flash with the result before the user is redirected to the home page.
    If `confirm()` is successful, then the user's ``confirmed`` attribute is set to ``True``.

    :param token: The JWT generated for the user when they first sign in.
    :type token: int
    """

    if current_user.confirmed:
        return redirect(url_for('main.index'))

    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')

    return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    """
    Handler to filter unconfirmed accounts if:
        1. A user is logged in (``current_user.is_authenticated`` is ``True``)
        2. The account for the user is not confirmed
        3. The requested URL is outside of the authentication blueprint and is not for a static file.
        Access to the authentication routes needs to be granted, as those are the routes that will enable
        the user to confirm the account or perform other account management functions.
    """
    if current_user.is_authenticated:
        current_user.ping()
    
        if not current_user.confirmed \
            and request.blueprint != 'auth' \
            and request.endpoint != 'static':
                return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))

    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    """ Route to resend the account confirmation email. """
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you via email.')
    return redirect(url_for('main.index'))

from flask import render_template, session, redirect, url_for, current_app, flash
from flask_login import login_required, current_user
from .. import db
from ..models import User, Role
from ..email import send_email
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm
from ..decorators import admin_required

@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()

        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False

            if current_app.config['FLASKY_ADMIN']:
                send_email(current_app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True

        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('.index'))

    return render_template('index.html',
        form=form,
        name=session.get('name'),
        known=session.get('known', False))

@main.route('/user/<username>')
def user(username):
    user_profile = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user_profile)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))

    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id: int):
    admin = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=admin)

    if form.validate_on_submit():
        admin.email = form.email.data
        admin.username = form.username.data
        admin.confirmed = form.confirmed.data
        admin.role = Role.query.get(form.role.data)
        admin.name = form.name.data
        admin.location = form.location.data
        admin.about_me = form.about_me.data

        db.session.add(admin)
        db.session.commit()

        flash('The profile has been updated.')

        return redirect(url_for('.user', username=admin.username))
    form.email.data = admin.email
    form.username.data = admin.username
    form.confirmed.data = admin.confirmed
    form.role.data = admin.role_id
    form.name.data = admin.name
    form.location.data = admin.location
    form.about_me.data = admin.about_me
    return render_template('edit_profile.html', form=form, user=user)

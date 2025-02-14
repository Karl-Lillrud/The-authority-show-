
from flask import g, redirect, render_template, url_for, Blueprint

dashboard_bp = Blueprint('dashboard_bp', __name__)

# 📌 Dashboard
@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('dashboard/dashboard.html')

# ✅ Serves the homepage page
@dashboard_bp.route('/homepage', methods=['GET'])
def homepage():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('dashboard/homepage.html')

# ✅ Serves the settings page
@dashboard_bp.route('/accountsettings', methods=['GET'])
def accountsettings():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('dashboard/accountsettings.html')

# ✅ Serves the profile page
@dashboard_bp.route('/podcastmanagement', methods=['GET'])
def podcastmanagement():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('dashboard/podcastmanagement.html')

# ✅ Serves the tasks page
@dashboard_bp.route('/taskmanagement', methods=['GET'])
def taskmanagement():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('dashboard/taskmanagement.html')

@dashboard_bp.route('/podprofile', methods=['GET', 'POST'])
def podprofile():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('podprofile/index.html')

@dashboard_bp.route('/team', methods=['GET', 'POST'])
def team():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('team/index.html')

@dashboard_bp.route('/guest', methods=['GET', 'POST'])
def guest():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))  # Fix: redirect using the blueprint route
    return render_template('guest/index.html')
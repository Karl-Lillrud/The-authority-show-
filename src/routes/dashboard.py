from flask import Flask, render_template, redirect, g, Blueprint
from routes.signin import signin_bp

dashboard_bp = Blueprint('dashboard_bp', __name__)

# 📌 Dashboard
@dashboard_bp.route('/dashboard', methods=['GET'],) #BP ROUTE?
def dashboard():
    if not g.user_id:
        return redirect(signin_bp)
    return render_template('dashboard/dashboard.html')
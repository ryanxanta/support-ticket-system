from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User, StaffUser

auth_bp = Blueprint('auth', __name__)


# ─── Customer Login ───────────────────────────────────────────────────────────

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('customer.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('auth/login.html')


# ─── Staff / Admin Login ──────────────────────────────────────────────────────

@auth_bp.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        staff = StaffUser.query.filter_by(username=username).first()
        if staff and check_password_hash(staff.password_hash, password):
            login_user(staff)
            if staff.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('staff.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('auth/staff_login.html')


# ─── Logout ───────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

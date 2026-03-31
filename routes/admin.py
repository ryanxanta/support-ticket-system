from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models import StaffUser, StaffSkill, Customer, CustomerSoftware, SoftwareType, Ticket, User
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isinstance(current_user, StaffUser) or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.staff_login'))
        return f(*args, **kwargs)
    return decorated


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
@require_admin
def dashboard():
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter(Ticket.status != 'Closed').count()
    total_customers = Customer.query.count()
    total_staff = StaffUser.query.filter_by(role='support').count()
    recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(10).all()
    all_staff = StaffUser.query.filter_by(role='support').all()
    return render_template('admin/dashboard.html',
                           total_tickets=total_tickets,
                           open_tickets=open_tickets,
                           total_customers=total_customers,
                           total_staff=total_staff,
                           recent_tickets=recent_tickets,
                           all_staff=all_staff)


# ─── Manage Staff ─────────────────────────────────────────────────────────────

@admin_bp.route('/staff')
@login_required
@require_admin
def manage_staff():
    staff_list = StaffUser.query.filter_by(role='support').all()
    all_software = SoftwareType.query.all()
    return render_template('admin/manage_staff.html', staff_list=staff_list, all_software=all_software)


@admin_bp.route('/staff/create', methods=['POST'])
@login_required
@require_admin
def create_staff():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        flash('Username and password required.', 'error')
        return redirect(url_for('admin.manage_staff'))
    if StaffUser.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('admin.manage_staff'))
    staff = StaffUser(username=username, password_hash=generate_password_hash(password), role='support')
    db.session.add(staff)
    db.session.commit()
    flash(f'Staff "{username}" created.', 'success')
    return redirect(url_for('admin.manage_staff'))


@admin_bp.route('/staff/<int:staff_id>/delete', methods=['POST'])
@login_required
@require_admin
def delete_staff(staff_id):
    staff = StaffUser.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    flash('Staff deleted.', 'success')
    return redirect(url_for('admin.manage_staff'))


@admin_bp.route('/staff/<int:staff_id>/skills', methods=['POST'])
@login_required
@require_admin
def update_staff_skills(staff_id):
    staff = StaffUser.query.get_or_404(staff_id)
    software_ids = request.form.getlist('software_ids', type=int)
    # Remove old skills
    StaffSkill.query.filter_by(staff_id=staff_id).delete()
    # Add new skills
    for sw_id in software_ids:
        db.session.add(StaffSkill(staff_id=staff_id, software_id=sw_id))
    db.session.commit()
    flash(f'Skills updated for {staff.username}.', 'success')
    return redirect(url_for('admin.manage_staff'))


# ─── Manage Customers ─────────────────────────────────────────────────────────

@admin_bp.route('/customers')
@login_required
@require_admin
def manage_customers():
    customers = Customer.query.all()
    all_software = SoftwareType.query.all()
    return render_template('admin/manage_customers.html', customers=customers, all_software=all_software)


@admin_bp.route('/customers/create', methods=['POST'])
@login_required
@require_admin
def create_customer():
    company_name = request.form.get('company_name', '').strip()
    phone = request.form.get('phone_number', '').strip()
    support_start = request.form.get('support_start')
    support_end = request.form.get('support_end')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not all([company_name, phone, support_start, support_end, username, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('admin.manage_customers'))

    from datetime import date
    cust = Customer(
        company_name=company_name,
        phone_number=phone,
        support_start=datetime.strptime(support_start, '%Y-%m-%d').date(),
        support_end=datetime.strptime(support_end, '%Y-%m-%d').date(),
    )
    db.session.add(cust)
    db.session.flush()

    user = User(username=username, password_hash=generate_password_hash(password), company_id=cust.id)
    db.session.add(user)
    db.session.commit()
    flash(f'Customer "{company_name}" created.', 'success')
    return redirect(url_for('admin.manage_customers'))


@admin_bp.route('/customer/<int:customer_id>/software', methods=['POST'])
@login_required
@require_admin
def update_customer_software(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    software_ids = request.form.getlist('software_ids', type=int)
    CustomerSoftware.query.filter_by(customer_id=customer_id).delete()
    for sw_id in software_ids:
        start_date_str = request.form.get(f'start_{sw_id}')
        end_date_str = request.form.get(f'end_{sw_id}')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else customer.support_start
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else customer.support_end

        db.session.add(CustomerSoftware(
            customer_id=customer_id, 
            software_id=sw_id,
            support_start=start_date,
            support_end=end_date
        ))
    db.session.commit()
    flash(f'Software updated for {customer.company_name}.', 'success')
    return redirect(url_for('admin.manage_customers'))


# ─── Manage Software (Skills) ──────────────────────────────────────────────────

@admin_bp.route('/software')
@login_required
@require_admin
def manage_software():
    all_software = SoftwareType.query.all()
    return render_template('admin/manage_software.html', all_software=all_software)

@admin_bp.route('/software/create', methods=['POST'])
@login_required
@require_admin
def create_software():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Software name required.', 'error')
        return redirect(url_for('admin.manage_software'))
    if SoftwareType.query.filter_by(name=name).first():
        flash('Software name already exists.', 'error')
        return redirect(url_for('admin.manage_software'))
    sw = SoftwareType(name=name)
    db.session.add(sw)
    db.session.commit()
    flash(f'Software "{name}" created.', 'success')
    return redirect(url_for('admin.manage_software'))

# ─── Admin Override Ticket ────────────────────────────────────────────────────

@admin_bp.route('/ticket/<int:ticket_id>/override', methods=['POST'])
@login_required
@require_admin
def override_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    new_staff_id = request.form.get('staff_id', type=int)
    if new_staff_id:
        ticket.assigned_to = new_staff_id
        ticket.assigned_at = datetime.utcnow()
        ticket.status = 'Assigned'
        db.session.commit()
        flash('Ticket reassigned by admin.', 'success')
    return redirect(url_for('admin.dashboard'))

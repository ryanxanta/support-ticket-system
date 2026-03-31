from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Ticket, Reply, CustomerSoftware, StaffSkill, StaffUser, SoftwareType
from utils import check_support_status, generate_ticket_no, generate_whatsapp_url
from datetime import datetime
import os

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx', 'zip'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def require_customer(f):
    """Decorator to ensure logged-in user is a customer."""
    from functools import wraps
    from models import User
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isinstance(current_user, User):
            flash('Access denied.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ────────────────────────────────────────────────────────────────

@customer_bp.route('/dashboard')
@login_required
@require_customer
def dashboard():
    customer = current_user.company
    status = check_support_status(customer)
    recent_tickets = Ticket.query.filter_by(company_id=customer.id).order_by(Ticket.created_at.desc()).limit(5).all()
    return render_template('customer/dashboard.html', customer=customer, status=status, recent_tickets=recent_tickets)


# ─── Submit Ticket ────────────────────────────────────────────────────────────

@customer_bp.route('/ticket/submit', methods=['GET', 'POST'])
@login_required
@require_customer
def submit_ticket():
    customer = current_user.company
    status = check_support_status(customer)
    owned_software = CustomerSoftware.query.filter_by(customer_id=customer.id).all()

    if request.method == 'POST':
        software_id = int(request.form.get('software_id'))
        description = request.form.get('description', '').strip()
        preferred_staff_id = request.form.get('preferred_staff_id') or None
        remote_tool = request.form.get('remote_tool') or None
        remote_id = request.form.get('remote_id', '').strip() or None
        remote_password = request.form.get('remote_password', '').strip() or None

        if not description:
            flash('Description is required.', 'error')
            return redirect(url_for('customer.submit_ticket'))

        # Handle file upload
        attachment = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                attachment = filename

        ticket_no = generate_ticket_no()
        preferred_status = 'Pending' if preferred_staff_id else None

        ticket = Ticket(
            ticket_no=ticket_no,
            company_id=customer.id,
            user_id=current_user.id,
            software_id=software_id,
            description=description,
            attachment=attachment,
            status='Open',
            support_status_at_creation=status,
            preferred_staff_id=int(preferred_staff_id) if preferred_staff_id else None,
            preferred_status=preferred_status,
            remote_tool=remote_tool,
            remote_id=remote_id,
            remote_password=remote_password
        )
        db.session.add(ticket)
        db.session.commit()
        flash(f'Ticket {ticket_no} submitted successfully!', 'success')
        return redirect(url_for('customer.ticket_detail', ticket_id=ticket.id))

    return render_template('customer/submit_ticket.html', customer=customer, status=status, owned_software=owned_software)


# ─── Ticket History ───────────────────────────────────────────────────────────

@customer_bp.route('/tickets')
@login_required
@require_customer
def ticket_history():
    customer = current_user.company
    status_filter = request.args.get('status', 'all')
    query = Ticket.query.filter_by(company_id=customer.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return render_template('customer/ticket_history.html', tickets=tickets, status_filter=status_filter)


# ─── Ticket Detail ────────────────────────────────────────────────────────────

@customer_bp.route('/ticket/<int:ticket_id>')
@login_required
@require_customer
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.company_id != current_user.company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('customer.ticket_history'))
    wa_url = generate_whatsapp_url(ticket)
    return render_template('customer/ticket_detail.html', ticket=ticket, wa_url=wa_url)


# ─── Customer Reply ───────────────────────────────────────────────────────────

@customer_bp.route('/ticket/<int:ticket_id>/reply', methods=['POST'])
@login_required
@require_customer
def reply_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.company_id != current_user.company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('customer.ticket_history'))
    message = request.form.get('message', '').strip()
    if not message:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))
    reply = Reply(
        ticket_id=ticket_id,
        sender='customer',
        sender_name=current_user.username,
        message=message,
    )
    db.session.add(reply)
    if ticket.status == 'Closed':
        ticket.status = 'In Progress'
    db.session.commit()
    flash('Reply sent.', 'success')
    return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))


# ─── API: Staff for Software ──────────────────────────────────────────────────

@customer_bp.route('/api/staff-for-software/<int:software_id>')
@login_required
def staff_for_software(software_id):
    skills = StaffSkill.query.filter_by(software_id=software_id).all()
    data = [{'id': s.staff_id, 'name': s.staff.username} for s in skills]
    return jsonify(data)

# ─── API: Fetch Replies ────────────────────────────────────────────────────────

@customer_bp.route('/api/ticket/<int:ticket_id>/replies')
@login_required
@require_customer
def api_ticket_replies(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.company_id != current_user.company_id:
        return jsonify({'error': 'Unauthorized'}), 403
    last_id = request.args.get('after', 0, type=int)
    new_replies = Reply.query.filter(Reply.ticket_id == ticket.id, Reply.id > last_id).order_by(Reply.id.asc()).all()
    
    data = []
    for r in new_replies:
        data.append({
            'id': r.id,
            'sender': r.sender,
            'sender_name': r.sender_name,
            'message': r.message,
            'time': r.created_at.strftime('%d %b %Y, %H:%M')
        })
    return jsonify({'replies': data})

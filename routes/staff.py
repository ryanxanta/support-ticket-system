from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Ticket, Reply, TransferRequest, StaffUser, StaffSkill, Customer
from utils import check_staff_skill, generate_whatsapp_url
from datetime import datetime

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


def require_staff(f):
    from functools import wraps
    from models import StaffUser
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isinstance(current_user, StaffUser):
            flash('Access denied.', 'error')
            return redirect(url_for('auth.staff_login'))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ────────────────────────────────────────────────────────────────

@staff_bp.route('/dashboard')
@login_required
@require_staff
def dashboard():
    staff = current_user
    my_software_ids = [s.software_id for s in staff.skills]

    tab = request.args.get('tab', 'unassigned')

    if tab == 'unassigned':
        tickets = Ticket.query.filter(
            Ticket.assigned_to == None,
            Ticket.status == 'Open',
            Ticket.software_id.in_(my_software_ids),
            Ticket.preferred_staff_id == None
        ).order_by(Ticket.created_at.desc()).all()

    elif tab == 'my_tickets':
        tickets = Ticket.query.filter(
            Ticket.assigned_to == staff.id,
            Ticket.status != 'Closed'
        ).order_by(Ticket.created_at.desc()).all()

    elif tab == 'unresolved':
        tickets = Ticket.query.filter(
            Ticket.status != 'Closed'
        ).order_by(Ticket.created_at.desc()).all()

    elif tab == 'closed':
        tickets = Ticket.query.filter_by(status='Closed').order_by(Ticket.created_at.desc()).all()

    elif tab == 'transfers':
        # Transfer requests directed TO current staff
        transfers = TransferRequest.query.filter_by(
            to_staff_id=staff.id,
            status='Pending'
        ).order_by(TransferRequest.created_at.desc()).all()
        transfer_count = len(transfers)
        customer_assigned_count = Ticket.query.filter_by(preferred_staff_id=staff.id, preferred_status='Pending').count()
        return render_template('staff/dashboard.html', tab=tab, transfers=transfers, tickets=[],
                               transfer_count=transfer_count, customer_assigned_count=customer_assigned_count)

    elif tab == 'customer_assigned':
        tickets = Ticket.query.filter(
            Ticket.preferred_staff_id == staff.id,
            Ticket.preferred_status == 'Pending'
        ).order_by(Ticket.created_at.desc()).all()

    else:
        tickets = []

    # Counts for badge
    transfer_count = TransferRequest.query.filter_by(to_staff_id=staff.id, status='Pending').count()
    customer_assigned_count = Ticket.query.filter_by(preferred_staff_id=staff.id, preferred_status='Pending').count()

    return render_template('staff/dashboard.html',
                           tab=tab,
                           tickets=tickets,
                           transfers=[],
                           transfer_count=transfer_count,
                           customer_assigned_count=customer_assigned_count)


# ─── Ticket Detail ────────────────────────────────────────────────────────────

@staff_bp.route('/ticket/<int:ticket_id>')
@login_required
@require_staff
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    staff = current_user
    all_staff = StaffUser.query.filter(StaffUser.id != staff.id, StaffUser.role == 'support').all()
    compatible_staff = [s for s in all_staff if s.has_skill(ticket.software_id)]
    active_transfer = TransferRequest.query.filter_by(ticket_id=ticket_id, status='Pending').first()
    wa_url = generate_whatsapp_url(ticket)
    return render_template('staff/ticket_detail.html',
                           ticket=ticket,
                           compatible_staff=compatible_staff,
                           active_transfer=active_transfer,
                           wa_url=wa_url)


# ─── Assign to Me ─────────────────────────────────────────────────────────────

@staff_bp.route('/ticket/<int:ticket_id>/assign', methods=['POST'])
@login_required
@require_staff
def assign_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    staff = current_user
    if ticket.assigned_to:
        flash('Ticket already assigned.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))
    if not staff.has_skill(ticket.software_id):
        flash('You do not have the skill for this software.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))
    ticket.assigned_to = staff.id
    ticket.assigned_at = datetime.utcnow()
    ticket.status = 'Assigned'
    db.session.commit()
    flash('Ticket assigned to you.', 'success')
    return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))


# ─── Reply ────────────────────────────────────────────────────────────────────

@staff_bp.route('/ticket/<int:ticket_id>/reply', methods=['POST'])
@login_required
@require_staff
def reply_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    staff = current_user
    if ticket.assigned_to != staff.id:
        flash('Only the assigned staff can reply.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))
    message = request.form.get('message', '').strip()
    if not message:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))
    reply = Reply(
        ticket_id=ticket_id,
        sender='staff',
        sender_name=staff.username,
        message=message,
    )
    db.session.add(reply)
    if ticket.status == 'Assigned':
        ticket.status = 'In Progress'
    db.session.commit()
    flash('Reply sent.', 'success')
    return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))


# ─── Close Ticket ─────────────────────────────────────────────────────────────

@staff_bp.route('/ticket/<int:ticket_id>/close', methods=['POST'])
@login_required
@require_staff
def close_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.assigned_to != current_user.id:
        flash('Only the assigned staff can close this ticket.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))
    ticket.status = 'Closed'
    ticket.closed_at = db.func.now()
    db.session.commit()
    flash('Ticket closed.', 'success')
    return redirect(url_for('staff.dashboard'))


# ─── Update Remark ────────────────────────────────────────────────────────────

@staff_bp.route('/ticket/<int:ticket_id>/remark', methods=['POST'])
@login_required
@require_staff
def update_remark(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.assigned_to != current_user.id:
        flash('Only the assigned staff can update remarks.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))
    remark = request.form.get('staff_remark', '').strip()
    ticket.staff_remark = remark
    db.session.commit()
    flash('Internal log updated.', 'success')
    return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))


# ─── API: Fetch Replies ────────────────────────────────────────────────────────

@staff_bp.route('/api/ticket/<int:ticket_id>/replies')
@login_required
@require_staff
def api_ticket_replies(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
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

# ─── Request Transfer ─────────────────────────────────────────────────────────

@staff_bp.route('/ticket/<int:ticket_id>/transfer', methods=['POST'])
@login_required
@require_staff
def request_transfer(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    staff = current_user
    if ticket.assigned_to != staff.id:
        flash('Only the assigned staff can request transfer.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))

    # Block if active transfer exists
    active = TransferRequest.query.filter_by(ticket_id=ticket_id, status='Pending').first()
    if active:
        flash('A transfer request is already pending.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))

    to_staff_id = int(request.form.get('to_staff_id'))
    to_staff = StaffUser.query.get_or_404(to_staff_id)
    if not to_staff.has_skill(ticket.software_id):
        flash('Target staff does not have the required skill.', 'error')
        return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))

    reason = request.form.get('reason', '').strip()
    tr = TransferRequest(
        ticket_id=ticket_id,
        from_staff_id=staff.id,
        to_staff_id=to_staff_id,
        reason=reason,
    )
    db.session.add(tr)
    db.session.commit()
    flash('Transfer request sent.', 'success')
    return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))


# ─── Approve Transfer ─────────────────────────────────────────────────────────

@staff_bp.route('/transfer/<int:request_id>/approve', methods=['POST'])
@login_required
@require_staff
def approve_transfer(request_id):
    tr = TransferRequest.query.get_or_404(request_id)
    if tr.to_staff_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('staff.dashboard', tab='transfers'))
    tr.status = 'Approved'
    tr.approved_at = datetime.utcnow()
    tr.ticket.assigned_to = current_user.id
    tr.ticket.assigned_at = datetime.utcnow()
    tr.ticket.status = 'Assigned'
    db.session.commit()
    flash('Transfer approved. Ticket assigned to you.', 'success')
    return redirect(url_for('staff.dashboard', tab='transfers'))


# ─── Reject Transfer ──────────────────────────────────────────────────────────

@staff_bp.route('/transfer/<int:request_id>/reject', methods=['POST'])
@login_required
@require_staff
def reject_transfer(request_id):
    tr = TransferRequest.query.get_or_404(request_id)
    if tr.to_staff_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('staff.dashboard', tab='transfers'))
    tr.status = 'Rejected'
    tr.approved_at = datetime.utcnow()
    db.session.commit()
    flash('Transfer rejected.', 'success')
    return redirect(url_for('staff.dashboard', tab='transfers'))


# ─── Accept Preferred ─────────────────────────────────────────────────────────

@staff_bp.route('/ticket/<int:ticket_id>/accept-preferred', methods=['POST'])
@login_required
@require_staff
def accept_preferred(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.preferred_staff_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('staff.dashboard'))
    ticket.assigned_to = current_user.id
    ticket.assigned_at = datetime.utcnow()
    ticket.status = 'Assigned'
    ticket.preferred_status = 'Accepted'
    db.session.commit()
    flash("You accepted the customer's preferred request.", 'success')
    return redirect(url_for('staff.ticket_detail', ticket_id=ticket_id))


# ─── Reject Preferred ────────────────────────────────────────────────────────

@staff_bp.route('/ticket/<int:ticket_id>/reject-preferred', methods=['POST'])
@login_required
@require_staff
def reject_preferred(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.preferred_staff_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('staff.dashboard'))
    ticket.preferred_status = 'Rejected'
    ticket.preferred_staff_id = None
    ticket.status = 'Open'
    db.session.commit()
    flash('Preferred request rejected. Ticket is back to Unassigned.', 'success')
    return redirect(url_for('staff.dashboard'))


# ─── Archive (Closed Tickets) ──────────────────────────────────────────────────

@staff_bp.route('/archive', methods=['GET'])
@login_required
@require_staff
def archive():
    # Filter constraints
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    company_id = request.args.get('company_id')
    
    query = Ticket.query.filter_by(status='Closed')
    
    if from_date:
        try:
            start = datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(Ticket.closed_at >= start)
        except ValueError:
            pass
            
    if to_date:
        try:
            # Add time boundary to cover the full end day
            end = datetime.strptime(to_date + " 23:59:59", '%Y-%m-%d %H:%M:%S')
            query = query.filter(Ticket.closed_at <= end)
        except ValueError:
            pass
            
    if company_id:
        query = query.filter(Ticket.company_id == company_id)
        
    tickets = query.order_by(Ticket.closed_at.desc(), Ticket.created_at.desc()).all()
    customers = Customer.query.order_by(Customer.company_name).all()
    
    return render_template('staff/archive.html', 
                          tickets=tickets, 
                          customers=customers,
                          from_date=from_date,
                          to_date=to_date,
                          company_id=company_id)


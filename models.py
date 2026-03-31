from extensions import db, login_manager
from flask_login import UserMixin
from datetime import date


# ─── Customer ────────────────────────────────────────────────────────────────

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), nullable=False)
    support_start = db.Column(db.Date, nullable=False)
    support_end = db.Column(db.Date, nullable=False)
    phone_number = db.Column(db.String(30), nullable=False)

    users = db.relationship('User', backref='company', lazy=True)
    tickets = db.relationship('Ticket', backref='company', lazy=True)
    software_links = db.relationship('CustomerSoftware', backref='customer', lazy=True)

    @property
    def support_status(self):
        return 'Active' if self.support_end >= date.today() else 'Expired'


# ─── Customer User ────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)

    def get_id(self):
        return f'user-{self.id}'


# ─── Staff User ───────────────────────────────────────────────────────────────

class StaffUser(UserMixin, db.Model):
    __tablename__ = 'staff_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='support')  # admin / support

    skills = db.relationship('StaffSkill', backref='staff', lazy=True)

    def get_id(self):
        return f'staff-{self.id}'

    def has_skill(self, software_id):
        return any(s.software_id == software_id for s in self.skills)


# ─── Software Types ───────────────────────────────────────────────────────────

class SoftwareType(db.Model):
    __tablename__ = 'software_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)


# ─── Customer Software ────────────────────────────────────────────────────────

class CustomerSoftware(db.Model):
    __tablename__ = 'customer_software'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    software_id = db.Column(db.Integer, db.ForeignKey('software_types.id'), nullable=False)
    support_start = db.Column(db.Date, nullable=False)
    support_end = db.Column(db.Date, nullable=False)

    software = db.relationship('SoftwareType')


# ─── Staff Skills ─────────────────────────────────────────────────────────────

class StaffSkill(db.Model):
    __tablename__ = 'staff_skills'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=False)
    software_id = db.Column(db.Integer, db.ForeignKey('software_types.id'), nullable=False)

    software = db.relationship('SoftwareType')


# ─── Tickets ──────────────────────────────────────────────────────────────────

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    ticket_no = db.Column(db.String(20), unique=True, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    software_id = db.Column(db.Integer, db.ForeignKey('software_types.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Normal')  # Low / Normal / High / Urgent
    attachment = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(30), default='Open')  # Open / Assigned / In Progress / Closed
    assigned_to = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    support_status_at_creation = db.Column(db.String(20), nullable=False)
    preferred_staff_id = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True)
    preferred_status = db.Column(db.String(20), nullable=True)  # Pending / Accepted / Rejected
    remote_tool = db.Column(db.String(50), nullable=True)
    remote_id = db.Column(db.String(50), nullable=True)
    remote_password = db.Column(db.String(50), nullable=True)
    staff_remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    closed_at = db.Column(db.DateTime, nullable=True)

    software = db.relationship('SoftwareType')
    submitter = db.relationship('User', foreign_keys=[user_id])
    assignee = db.relationship('StaffUser', foreign_keys=[assigned_to])
    preferred_staff = db.relationship('StaffUser', foreign_keys=[preferred_staff_id])
    replies = db.relationship('Reply', backref='ticket', lazy=True, order_by='Reply.created_at')
    transfer_requests = db.relationship('TransferRequest', backref='ticket', lazy=True)


# ─── Replies ──────────────────────────────────────────────────────────────────

class Reply(db.Model):
    __tablename__ = 'replies'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # customer / staff
    sender_name = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())


# ─── Transfer Requests ────────────────────────────────────────────────────────

class TransferRequest(db.Model):
    __tablename__ = 'transfer_requests'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    from_staff_id = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=False)
    to_staff_id = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending')  # Pending / Approved / Rejected
    created_at = db.Column(db.DateTime, default=db.func.now())
    approved_at = db.Column(db.DateTime, nullable=True)

    from_staff = db.relationship('StaffUser', foreign_keys=[from_staff_id])
    to_staff = db.relationship('StaffUser', foreign_keys=[to_staff_id])


# ─── Flask-Login Loader ───────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('staff-'):
        return StaffUser.query.get(int(user_id.split('-')[1]))
    elif user_id.startswith('user-'):
        return User.query.get(int(user_id.split('-')[1]))
    return None

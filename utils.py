from urllib.parse import quote
from datetime import date


def check_support_status(customer):
    """Returns 'Active' or 'Expired' based on support_end date."""
    return 'Active' if customer.support_end >= date.today() else 'Expired'


def check_staff_skill(staff, software_id):
    """Returns True if the staff member can handle the given software."""
    return any(s.software_id == software_id for s in staff.skills)


def generate_ticket_no():
    """Generate a sequential ticket number like TKT-0001."""
    from models import Ticket
    count = Ticket.query.count() + 1
    return f'TKT-{count:04d}'


def generate_whatsapp_url(ticket):
    """Build a WhatsApp click-to-chat URL with a pre-filled message."""
    phone = ticket.company.phone_number
    msg = (
        f"Hello {ticket.company.company_name},\n\n"
        f"Ticket #{ticket.ticket_no} ({ticket.software.name})\n\n"
        f"Issue: {ticket.description[:100]}\n\n"
        f"- Support Team"
    )
    return f"https://wa.me/{phone}?text={quote(msg)}"


PRIORITY_COLORS = {
    'Low': 'priority-low',
    'Normal': 'priority-normal',
    'High': 'priority-high',
    'Urgent': 'priority-urgent',
}

STATUS_COLORS = {
    'Open': 'status-open',
    'Assigned': 'status-assigned',
    'In Progress': 'status-inprogress',
    'Closed': 'status-closed',
}

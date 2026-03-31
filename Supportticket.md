# 🚀 MASTER SYSTEM BLUEPRINT

## Support Ticket System with WhatsApp + Staff Workflow + Skill Routing

---

# 🧩 1. Project Overview

## 🎯 Objective

Build a **professional support ticket system** that includes:

* Customer portal with login
* Ticket submission & tracking
* Support expiry management
* Staff multi-user system
* Skill-based ticket routing
* Ticket assignment & locking
* Transfer request + approval workflow
* Customer preferred staff selection
* WhatsApp integration (click-to-chat)

---

# 🏗️ 2. System Architecture

```text
Frontend (HTML / UI)
        ↓
Backend (Flask API)
        ↓
Database (SQLite → scalable)
        ↓
WhatsApp (Click-to-Chat)
```

---

# 👥 3. User Roles

---

## 👤 Customer

* Login
* View support status
* Submit ticket
* Select software
* (Optional) select preferred staff
* View ticket history

---

## 👨‍💼 Staff

* Login
* View tickets (filtered)
* Assign ticket
* Reply
* Request transfer
* Approve transfer

---

## 🧑‍💻 Admin

* Manage staff
* Assign software skills
* Assign customer software
* Override tickets

---

# 🗂️ 4. Database Schema

---

## 📌 customers

```sql
id
company_name
support_start
support_end
phone_number
```

---

## 📌 users (customer login)

```sql
id
username
password_hash
company_id
```

---

## 📌 staff_users

```sql
id
username
password_hash
role (admin / support)
```

---

## 📌 software_types

```sql
id
name
```

---

## 📌 customer_software

```sql
id
customer_id
software_id
```

---

## 📌 staff_skills

```sql
id
staff_id
software_id
```

---

## 📌 tickets

```sql
id
ticket_no
company_id
user_id
software_id
description
status (Open / Assigned / In Progress / Closed)
assigned_to
assigned_at
support_status_at_creation

preferred_staff_id
preferred_status (None / Pending / Accepted / Rejected)

created_at
```

---

## 📌 replies

```sql
id
ticket_id
sender (customer / staff)
message
created_at
```

---

## 📌 transfer_requests

```sql
id
ticket_id
from_staff_id
to_staff_id
status (Pending / Approved / Rejected)
created_at
approved_at
```

---

# 🔐 5. Authentication

---

## Customer Login

* Session: `user_id`

## Staff Login

* Session: `staff_id`

---

# 🧠 6. Support Expiry Logic

```python
if support_end < today:
    status = "Expired"
else:
    status = "Active"
```

---

## Behavior

| Status  | Action          |
| ------- | --------------- |
| Active  | Normal          |
| Expired | Allow + warning |

---

# 🖥️ 7. Customer Portal

---

## Dashboard

### Active

```
🟢 Support Active
Valid until: YYYY-MM-DD
```

### Expired

```
🔴 Support Expired
Expired on: YYYY-MM-DD

⚠️ You can still submit tickets
```

---

## Submit Ticket

### Fields:

* Software (filtered by owned software)
* Description
* Priority
* File upload
* Preferred staff (optional)

---

## Preferred Staff Rule

* Only show staff who support selected software

---

# 🎫 8. Ticket Lifecycle

```text
New → Unassigned
    ↓
(Customer Assigned - optional)
    ↓
Assigned
    ↓
In Progress
    ↓
Closed
```

---

# 🧑‍💼 9. Staff Dashboard

---

## Tabs

```text
[ Unassigned ]
[ My Tickets ]
[ Unresolved ]
[ Closed ]
[ Transfer Requests ]
[ Customer Assigned ]
```

---

## Definitions

* Unassigned → no owner
* My Tickets → assigned to me
* Unresolved → not closed
* Customer Assigned → waiting for acceptance

---

# 🎨 10. Ticket Card UI

---

## Example

```
TKT-0001
ABC Sdn Bhd

Software: SQL Accounting
Issue: Cannot print invoice

🟡 Unassigned
🔴 Expired Support

[ Assign to Me ]
```

---

## Customer Requested

```
⭐ Requested: John
⏳ Waiting Approval

[ Accept ] [ Reject ]
```

---

# 🔧 11. Assignment Logic

---

## Assign

```python
if ticket.assigned_to is None:
    if staff supports software:
        assign
```

---

## Locking

* Only assigned staff can:

  * Reply
  * Close

---

# 🔁 12. Transfer Workflow

---

## Request

```python
create transfer_request (Pending)
```

---

## Approve

```python
ticket.assigned_to = new_staff
status = Approved
```

---

## Reject

```python
status = Rejected
```

---

## Rules

* Only 1 active request
* Must match staff skill

---

# ⭐ 13. Customer Preferred Staff

---

## Submit

```python
preferred_status = "Pending"
```

---

## Accept

```python
assign to staff
preferred_status = "Accepted"
```

---

## Reject

```python
preferred_status = "Rejected"
→ back to Unassigned
```

---

# 🔒 14. Skill-Based Routing

---

## Rule

```python
if ticket.software_id not in staff.skills:
    block
```

---

# 💬 15. WhatsApp Integration

---

## URL

```
https://wa.me/{phone}?text={message}
```

---

## Button

```
[ Reply via WhatsApp ]
```

---

## Message Example

```
Hello ABC Sdn Bhd,

Ticket #TKT-0001 (SQL Accounting)

Issue: Cannot print invoice

Please restart your system.

- Support Team
```

---

# 🎨 16. UI Design

---

## Style

* Card-based
* Rounded (16px)
* Clean spacing
* Soft shadows

---

## Colors

| Status  | Color  |
| ------- | ------ |
| Active  | Green  |
| Expired | Red    |
| Pending | Yellow |

---

# 🔔 17. Notifications (Future)

* Transfer alerts
* New ticket alerts
* Expiry reminders

---

# 💰 18. Business Logic

---

## Expired Customers

* Allow ticket
* Show warning
* Trigger renewal

---

## Upsell Opportunity

* Promote renewal
* Promote additional modules

---

# 🚀 19. Development Roadmap

---

## Phase 1 (MVP)

* Login (customer + staff)
* Ticket submission
* Dashboard
* Assignment

---

## Phase 2

* Skill routing
* Transfer workflow
* Preferred staff

---

## Phase 3

* WhatsApp integration
* UI upgrade

---

## Phase 4

* Automation
* Analytics
* SLA

---

# 🧠 20. Key Principles

* Do not block users
* Keep workflow simple
* Ensure clear ownership
* Enforce skill validation
* Design for scaling

---

# 🎯 FINAL RESULT

A **complete SaaS-level support system** with:

* Customer portal
* Staff workflow system
* Smart assignment
* Transfer control
* WhatsApp integration
* Business-ready structure

---

# 🔥 END OF MASTER BLUEPRINT

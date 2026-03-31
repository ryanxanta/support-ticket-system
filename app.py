from flask import Flask
from datetime import date as _date
from werkzeug.security import generate_password_hash
from extensions import db, login_manager
import os


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecretkey-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///supportticket.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    # Make date.today available in all templates
    @app.context_processor
    def inject_globals():
        return {'today': _date.today()}

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from routes.auth import auth_bp
    from routes.customer import customer_bp
    from routes.staff import staff_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data():
    from models import StaffUser, SoftwareType, Customer, User, CustomerSoftware, StaffSkill
    from datetime import date, timedelta

    # Only seed if empty
    if StaffUser.query.first():
        return

    # Create software types
    softwares = ['SQL Accounting', 'AutoCount', 'SQL Payroll', 'UBS Accounting', 'MYOB']
    sw_objects = []
    for sw in softwares:
        s = SoftwareType(name=sw)
        db.session.add(s)
        sw_objects.append(s)
    db.session.flush()

    # Create admin
    admin = StaffUser(username='admin', password_hash=generate_password_hash('admin123'), role='admin')
    db.session.add(admin)

    # Create staff
    staff1 = StaffUser(username='john', password_hash=generate_password_hash('john123'), role='support')
    staff2 = StaffUser(username='sarah', password_hash=generate_password_hash('sarah123'), role='support')
    db.session.add_all([staff1, staff2])
    db.session.flush()

    # Assign skills
    db.session.add(StaffSkill(staff_id=staff1.id, software_id=sw_objects[0].id))
    db.session.add(StaffSkill(staff_id=staff1.id, software_id=sw_objects[1].id))
    db.session.add(StaffSkill(staff_id=staff2.id, software_id=sw_objects[0].id))
    db.session.add(StaffSkill(staff_id=staff2.id, software_id=sw_objects[2].id))

    # Create customers
    cust1 = Customer(
        company_name='ABC Sdn Bhd',
        support_start=date.today() - timedelta(days=180),
        support_end=date.today() + timedelta(days=185),
        phone_number='60123456789'
    )
    cust2 = Customer(
        company_name='XYZ Corporation',
        support_start=date.today() - timedelta(days=400),
        support_end=date.today() - timedelta(days=35),
        phone_number='60198765432'
    )
    db.session.add_all([cust1, cust2])
    db.session.flush()

    # Assign software to customers
    db.session.add(CustomerSoftware(
        customer_id=cust1.id, software_id=sw_objects[0].id,
        support_start=cust1.support_start, support_end=cust1.support_end
    ))
    db.session.add(CustomerSoftware(
        customer_id=cust1.id, software_id=sw_objects[1].id,
        support_start=cust1.support_start, support_end=cust1.support_end
    ))
    db.session.add(CustomerSoftware(
        customer_id=cust2.id, software_id=sw_objects[0].id,
        support_start=cust2.support_start, support_end=cust2.support_end
    ))
    db.session.add(CustomerSoftware(
        customer_id=cust2.id, software_id=sw_objects[2].id,
        support_start=cust2.support_start, support_end=cust2.support_end
    ))

    # Create customer users
    user1 = User(username='abc_user', password_hash=generate_password_hash('abc123'), company_id=cust1.id)
    user2 = User(username='xyz_user', password_hash=generate_password_hash('xyz123'), company_id=cust2.id)
    db.session.add_all([user1, user2])

    db.session.commit()
    print("✅ Seed data inserted.")


app = create_app()   # 👈 ADD THIS

if __name__ == '__main__':
    app.run(debug=True, port=5000)

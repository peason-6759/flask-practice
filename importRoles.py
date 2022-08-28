import os
from myvenv import create_app,db
from myvenv.models import Roles,Clients
from flask_migrate import Migrate
app=create_app(os.getenv('PEASON_CONFIG') or 'default')
migrate=Migrate(app,db)

with app.app_context():
    admin_role=Roles.query.filter_by(name='Administrator').first().rid
    default_role=Roles.query.filter_by(name='User').first().rid
    for u in Clients.query.all():
        if u.role is None:
            if u.email==app.config['PEASON_ADMIN']:
                u.role=admin_role
            else:
                u.role=default_role
    db.session.commit()
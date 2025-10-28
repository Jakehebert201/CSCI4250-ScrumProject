from authlib.integrations.flask_client import OAuth
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Centralized Flask extensions so they can be imported without causing circular imports.
db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()

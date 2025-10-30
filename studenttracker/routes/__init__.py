from .api import bp as api_bp
from .auth import bp as auth_bp
from .dashboards import bp as dashboards_bp


def register_blueprints(app):
    app.register_blueprint(dashboards_bp, url_prefix="/app")
    app.register_blueprint(auth_bp, url_prefix="/app")
    app.register_blueprint(api_bp, url_prefix="/app")

from . import api, auth, dashboards


def register_blueprints(app):
    auth.init_app(app)
    dashboards.init_app(app)
    api.init_app(app)

import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash

from studenttracker.extensions import db, migrate, oauth
from studenttracker.middleware import PrefixMiddleware
from studenttracker.routes import register_blueprints
from studenttracker.utils import register_template_filters
from wsgi_mount import ReverseProxied


def create_app():
    from dotenv import load_dotenv

    load_dotenv()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")
    raw_prefix = os.environ.get("APP_URL_PREFIX", "/app")
    configured_prefix = (raw_prefix or "").strip()
    if configured_prefix and not configured_prefix.startswith("/"):
        configured_prefix = f"/{configured_prefix}"
    if configured_prefix in {"", "/"}:
        normalized_prefix = ""
    else:
        normalized_prefix = configured_prefix.rstrip("/")
    static_url_path = f"{normalized_prefix}/static" if normalized_prefix else "/static"

    app = Flask(
        __name__,
        static_url_path=static_url_path,
        template_folder=template_dir,
        static_folder=static_dir,
    )
    app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key")
    app.wsgi_app = ReverseProxied(app.wsgi_app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1)
    app.config["APPLICATION_ROOT"] = normalized_prefix or "/"
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, default_prefix=normalized_prefix)

    default_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instance", "studenttracker.db"))
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID")
    app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET")

    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)

    oauth_enabled = bool(app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET"))
    if oauth_enabled:
        try:
            oauth.register(
                name="google",
                client_id=app.config["GOOGLE_CLIENT_ID"],
                client_secret=app.config["GOOGLE_CLIENT_SECRET"],
                server_metadata_url="https://accounts.google.com/.well-known/openid_configuration",
                client_kwargs={"scope": "openid email profile"},
            )
            app.logger.info("Google OAuth configured successfully")
        except Exception as exc:
            app.logger.error("Failed to configure Google OAuth: %s", exc)
            oauth_enabled = False
    else:
        app.logger.warning("Google OAuth not configured - OAuth login disabled")

    app.config["OAUTH_ENABLED"] = oauth_enabled
    app.jinja_env.globals["oauth_enabled"] = oauth_enabled

    register_template_filters(app)

    with app.app_context():
        from studenttracker import models  # noqa: F401
        from studenttracker.models import Professor, Student

        def ensure_seed_users():
            created = False

            if not Student.query.filter_by(username="student1").first():
                student = Student(
                    student_id="S0001",
                    username="student1",
                    password_hash=generate_password_hash("1234"),
                    email="student1@example.com",
                    first_name="Sample",
                    last_name="Student",
                    major="Computer Science",
                    year="Senior",
                )
                db.session.add(student)
                created = True

            if not Professor.query.filter_by(username="professor1").first():
                professor = Professor(
                    employee_id="P0001",
                    username="professor1",
                    password_hash=generate_password_hash("1234"),
                    email="professor1@example.com",
                    first_name="Sample",
                    last_name="Professor",
                    department="Computer Science",
                    title="Professor",
                )
                db.session.add(professor)
                created = True

            if created:
                db.session.commit()

        db.create_all()
        ensure_seed_users()

    register_blueprints(app)
    return app

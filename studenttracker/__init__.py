import os
from pathlib import Path

from flask import Flask, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash

from studenttracker.extensions import db, migrate, oauth
from studenttracker.routes import register_blueprints
from studenttracker.utils import register_template_filters


def create_app():
    from dotenv import load_dotenv

    load_dotenv()

    base_dir = Path(__file__).resolve().parent.parent

    app = Flask(
        __name__,
        static_folder=str(base_dir / "static"),
        static_url_path="/app/static",
        template_folder=str(base_dir / "templates"),
    )
    app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key")
    app.config["APPLICATION_ROOT"] = "/app"

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_port=1)
    app.config["PREFERRED_URL_SCHEME"] = "https"

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
                authorize_url="https://accounts.google.com/o/oauth2/auth",
                authorize_params=None,
                access_token_url="https://oauth2.googleapis.com/token",
                access_token_params=None,
                refresh_token_url=None,
                redirect_uri=None,
                client_kwargs={
                    "scope": "openid email profile",
                    "token_endpoint_auth_method": "client_secret_post"
                },
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
        from studenttracker.models import Professor, Student, Class

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

        def create_sample_data():
            """Create fake professors and classes for testing"""
            from datetime import time, date
            
            # Sample professors data
            professors_data = [
                {
                    "employee_id": "P1001",
                    "username": "dr_smith",
                    "email": "dr.smith@university.edu",
                    "first_name": "John",
                    "last_name": "Smith",
                    "department": "Computer Science",
                    "title": "Professor"
                },
                {
                    "employee_id": "P1002", 
                    "username": "prof_johnson",
                    "email": "m.johnson@university.edu",
                    "first_name": "Maria",
                    "last_name": "Johnson",
                    "department": "Computer Science",
                    "title": "Associate Professor"
                },
                {
                    "employee_id": "P1003",
                    "username": "dr_williams",
                    "email": "r.williams@university.edu", 
                    "first_name": "Robert",
                    "last_name": "Williams",
                    "department": "Mathematics",
                    "title": "Professor"
                },
                {
                    "employee_id": "P1004",
                    "username": "prof_davis",
                    "email": "s.davis@university.edu",
                    "first_name": "Sarah",
                    "last_name": "Davis",
                    "department": "Physics",
                    "title": "Assistant Professor"
                },
                {
                    "employee_id": "P1005",
                    "username": "dr_brown",
                    "email": "j.brown@university.edu",
                    "first_name": "James",
                    "last_name": "Brown",
                    "department": "Computer Science",
                    "title": "Lecturer"
                },
                {
                    "employee_id": "P1006",
                    "username": "prof_wilson",
                    "email": "l.wilson@university.edu",
                    "first_name": "Lisa",
                    "last_name": "Wilson",
                    "department": "Engineering",
                    "title": "Professor"
                }
            ]
            
            # Create professors if they don't exist
            created_professors = []
            for prof_data in professors_data:
                if not Professor.query.filter_by(email=prof_data["email"]).first():
                    professor = Professor(
                        employee_id=prof_data["employee_id"],
                        username=prof_data["username"],
                        password_hash=generate_password_hash("password123"),
                        email=prof_data["email"],
                        first_name=prof_data["first_name"],
                        last_name=prof_data["last_name"],
                        department=prof_data["department"],
                        title=prof_data["title"]
                    )
                    db.session.add(professor)
                    created_professors.append(professor)
            
            db.session.commit()
            
            # Get all professors for class assignment
            all_professors = Professor.query.all()
            
            # Sample classes data
            classes_data = [
                {
                    "course_code": "CSCI 1301",
                    "course_name": "Introduction to Programming",
                    "section": "001",
                    "description": "Fundamentals of programming using Python. Covers variables, control structures, functions, and basic data structures.",
                    "capacity": 35,
                    "credits": 3,
                    "meeting_days": "MWF",
                    "start_time": time(9, 0),
                    "end_time": time(9, 50),
                    "room": "CS 101",
                    "semester": "Fall",
                    "year": 2025
                },
                {
                    "course_code": "CSCI 2150",
                    "course_name": "Data Structures",
                    "section": "001", 
                    "description": "Study of fundamental data structures including arrays, linked lists, stacks, queues, trees, and graphs.",
                    "capacity": 30,
                    "credits": 3,
                    "meeting_days": "TTH",
                    "start_time": time(11, 0),
                    "end_time": time(12, 15),
                    "room": "CS 205",
                    "semester": "Fall",
                    "year": 2025
                },
                {
                    "course_code": "CSCI 3410",
                    "course_name": "Database Systems",
                    "section": "001",
                    "description": "Design and implementation of database systems. Covers SQL, normalization, transactions, and database administration.",
                    "capacity": 25,
                    "credits": 3,
                    "meeting_days": "MWF",
                    "start_time": time(14, 0),
                    "end_time": time(14, 50),
                    "room": "CS 301",
                    "semester": "Fall",
                    "year": 2025
                },
                {
                    "course_code": "CSCI 4250",
                    "course_name": "Software Engineering",
                    "section": "001",
                    "description": "Software development methodologies, project management, testing, and maintenance of large software systems.",
                    "capacity": 28,
                    "credits": 3,
                    "meeting_days": "TTH",
                    "start_time": time(15, 30),
                    "end_time": time(16, 45),
                    "room": "CS 401",
                    "semester": "Fall",
                    "year": 2025
                },
                {
                    "course_code": "MATH 2250",
                    "course_name": "Calculus II",
                    "section": "002",
                    "description": "Techniques of integration, applications of integrals, infinite sequences and series.",
                    "capacity": 40,
                    "credits": 4,
                    "meeting_days": "MTWF",
                    "start_time": time(10, 0),
                    "end_time": time(10, 50),
                    "room": "MATH 150",
                    "semester": "Fall",
                    "year": 2025
                },
                {
                    "course_code": "PHYS 2211",
                    "course_name": "Physics I",
                    "section": "001",
                    "description": "Mechanics, wave motion, and thermodynamics with calculus-based approach.",
                    "capacity": 32,
                    "credits": 4,
                    "meeting_days": "MWF",
                    "start_time": time(13, 0),
                    "end_time": time(13, 50),
                    "room": "PHYS 101",
                    "semester": "Fall",
                    "year": 2025
                },
                {
                    "course_code": "ENGR 1100",
                    "course_name": "Introduction to Engineering",
                    "section": "001",
                    "description": "Overview of engineering disciplines, problem-solving techniques, and engineering design process.",
                    "capacity": 45,
                    "credits": 2,
                    "meeting_days": "TTH",
                    "start_time": time(8, 0),
                    "end_time": time(9, 15),
                    "room": "ENGR 201",
                    "semester": "Fall",
                    "year": 2025
                },
                {
                    "course_code": "CSCI 3320",
                    "course_name": "Computer Networks",
                    "section": "001",
                    "description": "Network protocols, architecture, and security. Covers TCP/IP, routing, and network programming.",
                    "capacity": 24,
                    "credits": 3,
                    "meeting_days": "MWF",
                    "start_time": time(11, 0),
                    "end_time": time(11, 50),
                    "room": "CS 302",
                    "semester": "Spring",
                    "year": 2026
                }
            ]
            
            # Create classes if they don't exist
            for i, class_data in enumerate(classes_data):
                # Check if class already exists
                existing_class = Class.query.filter_by(
                    course_code=class_data["course_code"],
                    section=class_data["section"],
                    semester=class_data["semester"],
                    year=class_data["year"]
                ).first()
                
                if not existing_class:
                    # Assign professor based on department
                    professor = None
                    if "CSCI" in class_data["course_code"]:
                        cs_profs = [p for p in all_professors if p.department == "Computer Science"]
                        professor = cs_profs[i % len(cs_profs)] if cs_profs else all_professors[0]
                    elif "MATH" in class_data["course_code"]:
                        math_profs = [p for p in all_professors if p.department == "Mathematics"]
                        professor = math_profs[0] if math_profs else all_professors[0]
                    elif "PHYS" in class_data["course_code"]:
                        phys_profs = [p for p in all_professors if p.department == "Physics"]
                        professor = phys_profs[0] if phys_profs else all_professors[0]
                    elif "ENGR" in class_data["course_code"]:
                        engr_profs = [p for p in all_professors if p.department == "Engineering"]
                        professor = engr_profs[0] if engr_profs else all_professors[0]
                    else:
                        professor = all_professors[i % len(all_professors)]
                    
                    new_class = Class(
                        course_code=class_data["course_code"],
                        course_name=class_data["course_name"],
                        section=class_data["section"],
                        professor_id=professor.id,
                        semester=class_data["semester"],
                        year=class_data["year"],
                        room=class_data["room"],
                        description=class_data["description"],
                        capacity=class_data["capacity"],
                        credits=class_data["credits"],
                        meeting_days=class_data["meeting_days"],
                        start_time=class_data["start_time"],
                        end_time=class_data["end_time"],
                        start_date=date(2025, 8, 25),
                        end_date=date(2025, 12, 15),
                        is_active=True,
                        enrollment_open=True
                    )
                    db.session.add(new_class)
            
            db.session.commit()
            
            # Update existing classes that might have the old "Sample Professor"
            update_existing_classes()
            
            app.logger.info("Created sample professors and classes for testing")

        def update_existing_classes():
            """Update existing classes to use the new fake professors"""
            # Get the sample professor (old one)
            sample_prof = Professor.query.filter_by(username="professor1").first()
            
            # Get the new CS professors
            cs_professors = Professor.query.filter(
                Professor.department == "Computer Science",
                Professor.username != "professor1"
            ).all()
            
            if sample_prof and cs_professors:
                # Update Software Engineering class
                se_class = Class.query.filter_by(course_code="CSCI 4250", course_name="Software Engineering").first()
                if se_class and se_class.professor_id == sample_prof.id:
                    se_class.professor_id = cs_professors[0].id  # Dr. John Smith
                    app.logger.info(f"Updated Software Engineering class to be taught by {cs_professors[0].full_name}")
                
                # Update Introduction to Programming class if it exists
                intro_class = Class.query.filter_by(course_code="CSCI 1301", course_name="Introduction to Programming").first()
                if intro_class and intro_class.professor_id == sample_prof.id:
                    # Use a different professor for variety
                    prof_index = 1 if len(cs_professors) > 1 else 0
                    intro_class.professor_id = cs_professors[prof_index].id
                    app.logger.info(f"Updated Introduction to Programming class to be taught by {cs_professors[prof_index].full_name}")
                
                # Update any other classes taught by the sample professor
                other_classes = Class.query.filter_by(professor_id=sample_prof.id).all()
                for i, class_obj in enumerate(other_classes):
                    if class_obj.course_code.startswith("CSCI"):
                        # Assign to different CS professors
                        prof_index = i % len(cs_professors)
                        class_obj.professor_id = cs_professors[prof_index].id
                        app.logger.info(f"Updated {class_obj.full_course_name} to be taught by {cs_professors[prof_index].full_name}")
                
                db.session.commit()

        db.create_all()
        ensure_seed_users()
        
        # Create fake professors and classes for testing
        create_sample_data()

    register_blueprints(app)

    @app.route("/")
    def _redirect_root_to_app():
        return redirect(url_for("main.landing_page"))

    return app

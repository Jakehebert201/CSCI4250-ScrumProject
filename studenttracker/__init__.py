import os
from pathlib import Path

from flask import Flask, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash

from studenttracker.extensions import db, migrate, oauth, csrf, limiter
from studenttracker.routes import register_blueprints
from studenttracker.utils import register_template_filters


def create_app():
    from dotenv import load_dotenv
    from datetime import timedelta

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

    # Security configurations
    app.config.update(
        SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
        WTF_CSRF_TIME_LIMIT=None,  # CSRF tokens don't expire
        WTF_CSRF_SSL_STRICT=False,  # Allow development without HTTPS
    )

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
    csrf.init_app(app)
    limiter.init_app(app)

    # Security headers with Talisman (only in production)
    if os.environ.get("FLASK_ENV") == "production":
        from flask_talisman import Talisman
        Talisman(app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            content_security_policy={
                'default-src': "'self'",
                'script-src': ["'self'", "'unsafe-inline'", "https://maps.googleapis.com", "https://accounts.google.com"],
                'style-src': ["'self'", "'unsafe-inline'"],
                'img-src': ["'self'", "data:", "https:", "*.googleusercontent.com"],
                'connect-src': ["'self'", "https://maps.googleapis.com", "https://accounts.google.com"],
                'frame-src': ["'self'", "https://accounts.google.com"],
            },
            content_security_policy_nonce_in=['script-src']
        )

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
        from studenttracker.models import Professor, Student, Class, StudentLocation

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
            
            # Create diverse fake students
            create_fake_students()
            


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

                
                # Update Introduction to Programming class if it exists
                intro_class = Class.query.filter_by(course_code="CSCI 1301", course_name="Introduction to Programming").first()
                if intro_class and intro_class.professor_id == sample_prof.id:
                    # Use a different professor for variety
                    prof_index = 1 if len(cs_professors) > 1 else 0
                    intro_class.professor_id = cs_professors[prof_index].id

                
                # Update any other classes taught by the sample professor
                other_classes = Class.query.filter_by(professor_id=sample_prof.id).all()
                for i, class_obj in enumerate(other_classes):
                    if class_obj.course_code.startswith("CSCI"):
                        # Assign to different CS professors
                        prof_index = i % len(cs_professors)
                        class_obj.professor_id = cs_professors[prof_index].id

                
                db.session.commit()

        def create_fake_students():
            """Create diverse fake students from around the world"""
            import random
            from datetime import datetime
            
            # Diverse student data from different countries
            students_data = [
                {
                    "student_id": "S2001",
                    "username": "ahmad_hassan",
                    "email": "ahmad.hassan@university.edu",
                    "first_name": "Ahmad",
                    "last_name": "Hassan",
                    "major": "Computer Science",
                    "year": "Junior",
                    "country": "Afghanistan",
                    "lat": 34.5553,  # Kabul, Afghanistan
                    "lng": 69.2075,
                    "city": "Kabul"
                },
                {
                    "student_id": "S2002", 
                    "username": "dmitri_volkov",
                    "email": "dmitri.volkov@university.edu",
                    "first_name": "Dmitri",
                    "last_name": "Volkov",
                    "major": "Mathematics",
                    "year": "Senior",
                    "country": "Russia",
                    "lat": 55.7558,  # Moscow, Russia
                    "lng": 37.6176,
                    "city": "Moscow"
                },
                {
                    "student_id": "S2003",
                    "username": "emma_thompson",
                    "email": "emma.thompson@university.edu", 
                    "first_name": "Emma",
                    "last_name": "Thompson",
                    "major": "Engineering",
                    "year": "Sophomore",
                    "country": "England",
                    "lat": 51.5074,  # London, England
                    "lng": -0.1278,
                    "city": "London"
                },
                {
                    "student_id": "S2004",
                    "username": "amara_okafor",
                    "email": "amara.okafor@university.edu",
                    "first_name": "Amara",
                    "last_name": "Okafor", 
                    "major": "Biology",
                    "year": "Freshman",
                    "country": "Nigeria",
                    "lat": 6.5244,  # Lagos, Nigeria
                    "lng": 3.3792,
                    "city": "Lagos"
                },
                {
                    "student_id": "S2005",
                    "username": "hiroshi_tanaka",
                    "email": "hiroshi.tanaka@university.edu",
                    "first_name": "Hiroshi", 
                    "last_name": "Tanaka",
                    "major": "Computer Science",
                    "year": "Graduate",
                    "country": "Japan",
                    "lat": 35.6762,  # Tokyo, Japan
                    "lng": 139.6503,
                    "city": "Tokyo"
                },
                {
                    "student_id": "S2006",
                    "username": "maria_santos",
                    "email": "maria.santos@university.edu",
                    "first_name": "Maria",
                    "last_name": "Santos",
                    "major": "Psychology",
                    "year": "Junior",
                    "country": "Brazil",
                    "lat": -23.5505,  # São Paulo, Brazil
                    "lng": -46.6333,
                    "city": "São Paulo"
                },
                {
                    "student_id": "S2007",
                    "username": "pierre_dubois",
                    "email": "pierre.dubois@university.edu",
                    "first_name": "Pierre",
                    "last_name": "Dubois",
                    "major": "Physics",
                    "year": "Senior",
                    "country": "France",
                    "lat": 48.8566,  # Paris, France
                    "lng": 2.3522,
                    "city": "Paris"
                },
                {
                    "student_id": "S2008",
                    "username": "priya_sharma",
                    "email": "priya.sharma@university.edu",
                    "first_name": "Priya",
                    "last_name": "Sharma",
                    "major": "Computer Science",
                    "year": "Sophomore",
                    "country": "India",
                    "lat": 28.7041,  # New Delhi, India
                    "lng": 77.1025,
                    "city": "New Delhi"
                },
                {
                    "student_id": "S2009",
                    "username": "carlos_rodriguez",
                    "email": "carlos.rodriguez@university.edu",
                    "first_name": "Carlos",
                    "last_name": "Rodriguez",
                    "major": "Business",
                    "year": "Junior",
                    "country": "Mexico",
                    "lat": 19.4326,  # Mexico City, Mexico
                    "lng": -99.1332,
                    "city": "Mexico City"
                },
                {
                    "student_id": "S2010",
                    "username": "fatima_al_zahra",
                    "email": "fatima.alzahra@university.edu",
                    "first_name": "Fatima",
                    "last_name": "Al-Zahra",
                    "major": "Medicine",
                    "year": "Graduate",
                    "country": "UAE",
                    "lat": 25.2048,  # Dubai, UAE
                    "lng": 55.2708,
                    "city": "Dubai"
                },
                {
                    "student_id": "S2011",
                    "username": "lars_andersen",
                    "email": "lars.andersen@university.edu",
                    "first_name": "Lars",
                    "last_name": "Andersen",
                    "major": "Environmental Science",
                    "year": "Senior",
                    "country": "Norway",
                    "lat": 59.9139,  # Oslo, Norway
                    "lng": 10.7522,
                    "city": "Oslo"
                },
                {
                    "student_id": "S2012",
                    "username": "chen_wei",
                    "email": "chen.wei@university.edu",
                    "first_name": "Chen",
                    "last_name": "Wei",
                    "major": "Engineering",
                    "year": "Freshman",
                    "country": "China",
                    "lat": 39.9042,  # Beijing, China
                    "lng": 116.4074,
                    "city": "Beijing"
                },
                {
                    "student_id": "S2013",
                    "username": "sophia_mueller",
                    "email": "sophia.mueller@university.edu",
                    "first_name": "Sophia",
                    "last_name": "Mueller",
                    "major": "Art History",
                    "year": "Junior",
                    "country": "Germany",
                    "lat": 52.5200,  # Berlin, Germany
                    "lng": 13.4050,
                    "city": "Berlin"
                },
                {
                    "student_id": "S2014",
                    "username": "kofi_asante",
                    "email": "kofi.asante@university.edu",
                    "first_name": "Kofi",
                    "last_name": "Asante",
                    "major": "Economics",
                    "year": "Sophomore",
                    "country": "Ghana",
                    "lat": 5.6037,  # Accra, Ghana
                    "lng": -0.1870,
                    "city": "Accra"
                },
                {
                    "student_id": "S2015",
                    "username": "isabella_rossi",
                    "email": "isabella.rossi@university.edu",
                    "first_name": "Isabella",
                    "last_name": "Rossi",
                    "major": "Architecture",
                    "year": "Senior",
                    "country": "Italy",
                    "lat": 41.9028,  # Rome, Italy
                    "lng": 12.4964,
                    "city": "Rome"
                }
            ]
            
            # Create students if they don't exist
            created_count = 0
            for student_data in students_data:
                if not Student.query.filter_by(email=student_data["email"]).first():
                    student = Student(
                        student_id=student_data["student_id"],
                        username=student_data["username"],
                        password_hash=generate_password_hash("password123"),
                        email=student_data["email"],
                        first_name=student_data["first_name"],
                        last_name=student_data["last_name"],
                        major=student_data["major"],
                        year=student_data["year"],
                        last_lat=student_data["lat"],
                        last_lng=student_data["lng"],
                        last_seen=datetime.utcnow()
                    )
                    db.session.add(student)
                    created_count += 1
                    
            if created_count > 0:
                db.session.commit()

                
            # Always ensure all fake students have location entries (even if students already existed)
            locations_created = 0
            for student_data in students_data:
                student = Student.query.filter_by(email=student_data["email"]).first()
                if student and not StudentLocation.query.filter_by(student_id=student.id).first():
                    # Create fake location with older timestamp (6+ hours ago) so it appears as "last active"
                    hours_ago = random.randint(6, 48)  # 6 to 48 hours ago
                    old_timestamp = datetime.utcnow() - timedelta(hours=hours_ago)
                    
                    location = StudentLocation(
                        student_id=student.id,
                        lat=student_data["lat"],
                        lng=student_data["lng"],
                        accuracy=random.randint(10, 50),
                        city=student_data["city"],
                        notes=f"International student from {student_data['country']}",
                        created_at=old_timestamp
                    )
                    db.session.add(location)
                    locations_created += 1
            
            if locations_created > 0:
                db.session.commit()

                
                # Create additional fake locations to populate the map
                create_additional_fake_locations()

        def create_additional_fake_locations():
            """Create additional fake location entries to populate the map"""
            import random
            from datetime import datetime, timedelta
            
            # Get all students
            all_students = Student.query.all()
            
            # Additional interesting locations around the world
            fake_locations = [
                # Major cities
                {"lat": 40.7128, "lng": -74.0060, "city": "New York City", "country": "USA"},
                {"lat": 34.0522, "lng": -118.2437, "city": "Los Angeles", "country": "USA"},
                {"lat": 41.8781, "lng": -87.6298, "city": "Chicago", "country": "USA"},
                {"lat": 37.7749, "lng": -122.4194, "city": "San Francisco", "country": "USA"},
                {"lat": 25.7617, "lng": -80.1918, "city": "Miami", "country": "USA"},
                
                # International locations
                {"lat": -33.8688, "lng": 151.2093, "city": "Sydney", "country": "Australia"},
                {"lat": -37.8136, "lng": 144.9631, "city": "Melbourne", "country": "Australia"},
                {"lat": 43.6532, "lng": -79.3832, "city": "Toronto", "country": "Canada"},
                {"lat": 45.5017, "lng": -73.5673, "city": "Montreal", "country": "Canada"},
                {"lat": 49.2827, "lng": -123.1207, "city": "Vancouver", "country": "Canada"},
                
                # European cities
                {"lat": 52.3676, "lng": 4.9041, "city": "Amsterdam", "country": "Netherlands"},
                {"lat": 59.3293, "lng": 18.0686, "city": "Stockholm", "country": "Sweden"},
                {"lat": 55.6761, "lng": 12.5683, "city": "Copenhagen", "country": "Denmark"},
                {"lat": 60.1699, "lng": 24.9384, "city": "Helsinki", "country": "Finland"},
                {"lat": 50.0755, "lng": 14.4378, "city": "Prague", "country": "Czech Republic"},
                
                # Asian cities
                {"lat": 1.3521, "lng": 103.8198, "city": "Singapore", "country": "Singapore"},
                {"lat": 22.3193, "lng": 114.1694, "city": "Hong Kong", "country": "Hong Kong"},
                {"lat": 37.5665, "lng": 126.9780, "city": "Seoul", "country": "South Korea"},
                {"lat": 25.0330, "lng": 121.5654, "city": "Taipei", "country": "Taiwan"},
                {"lat": 13.7563, "lng": 100.5018, "city": "Bangkok", "country": "Thailand"},
                
                # Campus-like locations (universities)
                {"lat": 42.3601, "lng": -71.0589, "city": "Boston (MIT)", "country": "USA"},
                {"lat": 37.4275, "lng": -122.1697, "city": "Stanford", "country": "USA"},
                {"lat": 37.8719, "lng": -122.2585, "city": "Berkeley", "country": "USA"},
                {"lat": 51.7548, "lng": -1.2544, "city": "Oxford", "country": "UK"},
                {"lat": 52.2043, "lng": 0.1218, "city": "Cambridge", "country": "UK"},
            ]
            
            # Create multiple location entries for students to show movement
            location_count = 0
            for student in all_students[:10]:  # Add locations for first 10 students
                # Add 2-4 random locations per student
                num_locations = random.randint(2, 4)
                
                for i in range(num_locations):
                    # Choose a random location
                    location_data = random.choice(fake_locations)
                    
                    # Add some random variation to coordinates (within ~1km)
                    lat_variation = random.uniform(-0.01, 0.01)
                    lng_variation = random.uniform(-0.01, 0.01)
                    
                    # Create timestamp in the past few days
                    days_ago = random.randint(1, 7)
                    hours_ago = random.randint(0, 23)
                    timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
                    
                    # Check if this location already exists for this student
                    existing = StudentLocation.query.filter_by(
                        student_id=student.id,
                        city=location_data["city"]
                    ).first()
                    
                    if not existing:
                        fake_location = StudentLocation(
                            student_id=student.id,
                            lat=location_data["lat"] + lat_variation,
                            lng=location_data["lng"] + lng_variation,
                            accuracy=random.randint(5, 100),
                            city=location_data["city"],
                            notes=f"Visited {location_data['city']}, {location_data['country']}",
                            created_at=timestamp
                        )
                        db.session.add(fake_location)
                        location_count += 1
            
            # Add some recent campus locations (simulate students on campus)
            campus_locations = [
                {"lat": 33.7490, "lng": -84.3880, "city": "Atlanta Campus - Library", "country": "USA"},
                {"lat": 33.7495, "lng": -84.3885, "city": "Atlanta Campus - Student Center", "country": "USA"},
                {"lat": 33.7485, "lng": -84.3875, "city": "Atlanta Campus - Engineering Building", "country": "USA"},
                {"lat": 33.7500, "lng": -84.3890, "city": "Atlanta Campus - Science Lab", "country": "USA"},
                {"lat": 33.7480, "lng": -84.3870, "city": "Atlanta Campus - Cafeteria", "country": "USA"},
            ]
            
            # Add recent campus locations for some students
            for student in all_students[5:15]:  # Different set of students
                campus_location = random.choice(campus_locations)
                
                # Recent timestamp (within last 24 hours)
                hours_ago = random.randint(1, 24)
                timestamp = datetime.utcnow() - timedelta(hours=hours_ago)
                
                recent_location = StudentLocation(
                    student_id=student.id,
                    lat=campus_location["lat"] + random.uniform(-0.001, 0.001),
                    lng=campus_location["lng"] + random.uniform(-0.001, 0.001),
                    accuracy=random.randint(5, 25),
                    city=campus_location["city"],
                    notes="On campus activity",
                    created_at=timestamp
                )
                db.session.add(recent_location)
                location_count += 1
            
            if location_count > 0:
                db.session.commit()


        db.create_all()
        
        # Create fake professors and classes for testing
        create_sample_data()
        
        # Setup notifications
        from studenttracker.utils import create_default_notification_types
        create_default_notification_types()

    register_blueprints(app)

    @app.route("/")
    def _redirect_root_to_app():
        return redirect(url_for("main.landing_page"))

    return app

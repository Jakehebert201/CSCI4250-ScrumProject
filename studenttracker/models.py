from datetime import datetime

from werkzeug.security import check_password_hash

from .extensions import db


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    major = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(20), nullable=True)
    last_lat = db.Column(db.Float, nullable=True)
    last_lng = db.Column(db.Float, nullable=True)
    last_accuracy = db.Column(db.Float, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    oauth_provider = db.Column(db.String(50), nullable=True)

    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_oauth_user(self):
        return self.oauth_provider is not None


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    oauth_provider = db.Column(db.String(50), nullable=True)

    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_oauth_user(self):
        return self.oauth_provider is not None


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), nullable=False)
    course_name = db.Column(db.String(200), nullable=False)
    section = db.Column(db.String(10), nullable=True)
    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    room = db.Column(db.String(50), nullable=True)
    schedule = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    professor = db.relationship("Professor", backref=db.backref("classes", lazy="dynamic"))

    @property
    def full_course_name(self):
        return f"{self.course_code}: {self.course_name}"


class StudentLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    city = db.Column(db.String(255), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey("class.id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", backref=db.backref("locations", lazy="dynamic"))
    class_attended = db.relationship("Class", backref=db.backref("student_locations", lazy="dynamic"))


class ClockEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)

    student = db.relationship("Student", backref=db.backref("clock_events", lazy="dynamic"))


class DailyCampusTime(db.Model):
    __table_args__ = (
        db.UniqueConstraint("student_id", "day", name="uq_daily_campus_time_student_day"),
    )
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    day = db.Column(db.Date, nullable=False)
    total_seconds = db.Column(db.Integer, nullable=False, default=0)

    student = db.relationship("Student", backref=db.backref("daily_campus_times", lazy="dynamic"))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    last_lat = db.Column(db.Float, nullable=True)
    last_lng = db.Column(db.Float, nullable=True)
    last_accuracy = db.Column(db.Float, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    city = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("locations", lazy="dynamic"))

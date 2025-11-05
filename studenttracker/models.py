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


# Association table for student-class enrollment (many-to-many)
student_class_enrollment = db.Table('student_class_enrollment',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('enrolled_at', db.DateTime, default=datetime.utcnow, nullable=False),
    db.Column('status', db.String(20), default='active', nullable=False)  # active, dropped, completed
)


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
    
    # Enhanced class details
    description = db.Column(db.Text, nullable=True)
    capacity = db.Column(db.Integer, default=30, nullable=False)
    credits = db.Column(db.Integer, default=3, nullable=False)
    meeting_days = db.Column(db.String(20), nullable=True)  # e.g., "MWF", "TTH"
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    enrollment_open = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    professor = db.relationship("Professor", backref=db.backref("classes", lazy="dynamic"))
    enrolled_students = db.relationship("Student", 
                                      secondary=student_class_enrollment, 
                                      backref=db.backref("enrolled_classes", lazy="dynamic"),
                                      lazy="dynamic")

    @property
    def full_course_name(self):
        return f"{self.course_code}: {self.course_name}"
    
    @property
    def enrollment_count(self):
        return self.enrolled_students.count()
    
    @property
    def is_full(self):
        return self.enrollment_count >= self.capacity
    
    @property
    def available_spots(self):
        return max(0, self.capacity - self.enrollment_count)
    
    def is_student_enrolled(self, student):
        return self.enrolled_students.filter_by(id=student.id).first() is not None
    
    def enroll_student(self, student):
        if not self.is_student_enrolled(student) and not self.is_full and self.enrollment_open:
            self.enrolled_students.append(student)
            return True
        return False
    
    def drop_student(self, student):
        if self.is_student_enrolled(student):
            self.enrolled_students.remove(student)
            return True
        return False


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


# Notification Models
class NotificationType(db.Model):
    __tablename__ = 'notification_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(20), default='🔔')
    color = db.Column(db.String(7), default='#3b82f6')  # Hex color
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationType {self.name}>'


class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Recipients
    user_id = db.Column(db.Integer, nullable=True)  # Specific user (null for broadcast)
    user_type = db.Column(db.String(20), nullable=True)  # 'student', 'professor', or null for all
    
    # Content
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(20), default='🔔')
    
    # Type and Priority
    type_id = db.Column(db.Integer, db.ForeignKey('notification_type.id'), nullable=True)
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    
    # Actions
    action_url = db.Column(db.String(200), nullable=True)
    action_text = db.Column(db.String(50), nullable=True)
    secondary_action_url = db.Column(db.String(200), nullable=True)
    secondary_action_text = db.Column(db.String(50), nullable=True)
    
    # Metadata
    data = db.Column(db.JSON, nullable=True)  # Additional data (class_id, location, etc.)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Scheduling
    scheduled_for = db.Column(db.DateTime, nullable=True)  # For future notifications
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notification_type = db.relationship('NotificationType', backref='notifications')
    
    @property
    def is_expired(self):
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    @property
    def priority_color(self):
        colors = {
            'low': '#6b7280',
            'normal': '#3b82f6', 
            'high': '#f59e0b',
            'urgent': '#ef4444'
        }
        return colors.get(self.priority, '#3b82f6')
    
    @property
    def priority_icon(self):
        icons = {
            'low': '💬',
            'normal': '🔔',
            'high': '⚠️',
            'urgent': '🚨'
        }
        return icons.get(self.priority, '🔔')
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'icon': self.icon,
            'priority': self.priority,
            'priority_color': self.priority_color,
            'priority_icon': self.priority_icon,
            'action_url': self.action_url,
            'action_text': self.action_text,
            'secondary_action_url': self.secondary_action_url,
            'secondary_action_text': self.secondary_action_text,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'data': self.data
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class UserNotificationPreference(db.Model):
    __tablename__ = 'user_notification_preference'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'student' or 'professor'
    
    # Notification channels
    browser_push_enabled = db.Column(db.Boolean, default=True)
    email_enabled = db.Column(db.Boolean, default=True)
    in_app_enabled = db.Column(db.Boolean, default=True)
    
    # Notification types (JSON array of enabled type IDs)
    enabled_types = db.Column(db.JSON, default=lambda: [])
    
    # Timing preferences
    quiet_hours_start = db.Column(db.Time, nullable=True)  # e.g., 22:00
    quiet_hours_end = db.Column(db.Time, nullable=True)    # e.g., 07:00
    
    # Frequency settings
    digest_frequency = db.Column(db.String(20), default='daily')  # 'realtime', 'hourly', 'daily', 'weekly'
    
    # Class-specific settings
    class_reminders_enabled = db.Column(db.Boolean, default=True)
    class_reminder_minutes = db.Column(db.Integer, default=15)  # Minutes before class
    
    # Location settings
    location_alerts_enabled = db.Column(db.Boolean, default=True)
    attendance_alerts_enabled = db.Column(db.Boolean, default=True)
    
    # Emergency settings
    emergency_notifications_enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserNotificationPreference user_id={self.user_id}>'


class PushSubscription(db.Model):
    __tablename__ = 'push_subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    
    # Push subscription data
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    
    # Browser/device info
    user_agent = db.Column(db.Text, nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    device_type = db.Column(db.String(20), nullable=True)  # 'desktop', 'mobile', 'tablet'
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PushSubscription user_id={self.user_id}>'

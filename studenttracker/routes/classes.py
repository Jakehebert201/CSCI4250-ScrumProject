from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from datetime import datetime, time, date

from studenttracker.extensions import db
from studenttracker.models import Class, Professor, Student

bp = Blueprint("classes", __name__)

print("🎓 Classes blueprint created!")


@bp.route("/test")
def test_classes():
    """Test route to verify classes blueprint is working"""
    from flask import current_app
    
    # List all registered routes
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append(f"{rule.rule} -> {rule.endpoint}")
    
    routes_html = "<br>".join(routes)
    
    return f"""
    <h1>Classes Blueprint Working!</h1>
    <p>User ID: {session.get('user_id')}</p>
    <p>User Type: {session.get('user_type')}</p>
    <h2>All Registered Routes:</h2>
    <div style="font-family: monospace; font-size: 12px;">
        {routes_html}
    </div>
    """


def require_professor():
    """Decorator to ensure only professors can access certain routes"""
    if not session.get("user_id") or session.get("user_type") != "professor":
        flash("Access denied. Professor login required.")
        return redirect(url_for("auth.login"))
    return None


def require_student():
    """Decorator to ensure only students can access certain routes"""
    if not session.get("user_id") or session.get("user_type") != "student":
        flash("Access denied. Student login required.")
        return redirect(url_for("auth.login"))
    return None


@bp.route("/")
def list_classes():
    """List all available classes"""
    try:
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        
        user_type = session.get("user_type")
        
        if user_type == "professor":
            # Professors see their own classes
            professor = Professor.query.get(session.get("user_id"))
            classes = professor.classes.all() if professor else []
            return render_template("classes/professor_classes.html", classes=classes, professor=professor)
        
        elif user_type == "student":
            # Students see all available classes and their enrolled classes
            student = Student.query.get(session.get("user_id"))
            if not student:
                current_app.logger.error(f"Student with ID {session.get('user_id')} not found in database")
                return redirect(url_for("auth.login"))
                
            all_classes = Class.query.filter_by(is_active=True).all()
            enrolled_classes = student.enrolled_classes.all() if student else []
            
            return render_template("classes/student_classes.html", 
                                 all_classes=all_classes, 
                                 enrolled_classes=enrolled_classes,
                                 student=student)
        
        return redirect(url_for("auth.login"))
        
    except Exception as e:
        current_app.logger.error(f"Error in classes route: {str(e)}")
        return redirect(url_for("main.landing_page"))


@bp.route("/create", methods=["GET", "POST"])
def create_class():
    """Create a new class (professors only)"""
    auth_check = require_professor()
    if auth_check:
        return auth_check
    
    professor = Professor.query.get(session.get("user_id"))
    
    if request.method == "POST":
        try:
            # Parse form data
            course_code = request.form.get("course_code", "").strip()
            course_name = request.form.get("course_name", "").strip()
            section = request.form.get("section", "").strip()
            semester = request.form.get("semester", "").strip()
            year = int(request.form.get("year", datetime.now().year))
            room = request.form.get("room", "").strip()
            description = request.form.get("description", "").strip()
            capacity = int(request.form.get("capacity", 30))
            credits = int(request.form.get("credits", 3))
            meeting_days = request.form.get("meeting_days", "").strip()
            
            # Parse times
            start_time_str = request.form.get("start_time")
            end_time_str = request.form.get("end_time")
            start_date_str = request.form.get("start_date")
            end_date_str = request.form.get("end_date")
            
            start_time = datetime.strptime(start_time_str, "%H:%M").time() if start_time_str else None
            end_time = datetime.strptime(end_time_str, "%H:%M").time() if end_time_str else None
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
            
            # Validation
            if not all([course_code, course_name, semester]):
                flash("Course code, name, and semester are required.")
                return render_template("classes/create_class.html", professor=professor)
            
            # Create the class
            new_class = Class(
                course_code=course_code,
                course_name=course_name,
                section=section or None,
                professor_id=professor.id,
                semester=semester,
                year=year,
                room=room or None,
                description=description or None,
                capacity=capacity,
                credits=credits,
                meeting_days=meeting_days or None,
                start_time=start_time,
                end_time=end_time,
                start_date=start_date,
                end_date=end_date
            )
            
            db.session.add(new_class)
            db.session.commit()
            
            flash(f"Class '{new_class.full_course_name}' created successfully!")
            return redirect(url_for("classes.list_classes"))
            
        except ValueError as e:
            flash(f"Invalid input: {str(e)}")
        except Exception as e:
            flash(f"Error creating class: {str(e)}")
            db.session.rollback()
    
    return render_template("classes/create_class.html", professor=professor)


@bp.route("/<int:class_id>")
def view_class(class_id):
    """View class details"""
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    
    class_obj = Class.query.get_or_404(class_id)
    user_type = session.get("user_type")
    user_id = session.get("user_id")
    
    # Check permissions
    if user_type == "professor":
        professor = Professor.query.get(user_id)
        if class_obj.professor_id != professor.id:
            flash("You can only view your own classes.")
            return redirect(url_for("classes.list_classes"))
        
        enrolled_students = class_obj.enrolled_students.all()
        return render_template("classes/class_detail_professor.html", 
                             class_obj=class_obj, 
                             enrolled_students=enrolled_students,
                             professor=professor)
    
    elif user_type == "student":
        student = Student.query.get(user_id)
        is_enrolled = class_obj.is_student_enrolled(student)
        return render_template("classes/class_detail_student.html", 
                             class_obj=class_obj, 
                             is_enrolled=is_enrolled,
                             student=student)
    
    return redirect(url_for("auth.login"))


@bp.route("/<int:class_id>/enroll", methods=["POST"])
def enroll_in_class(class_id):
    """Enroll student in a class"""
    auth_check = require_student()
    if auth_check:
        return auth_check
    
    student = Student.query.get(session.get("user_id"))
    class_obj = Class.query.get_or_404(class_id)
    
    if class_obj.enroll_student(student):
        db.session.commit()
        flash(f"Successfully enrolled in {class_obj.full_course_name}!")
        
        # Create enrollment notification for student
        from studenttracker.services.notification_service import notification_service
        notification_service.create_notification(
            title="Successfully Enrolled! 🎓",
            message=f"You've been enrolled in {class_obj.full_course_name}\nRoom: {class_obj.room or 'TBD'} | {class_obj.meeting_days or 'Schedule TBD'}",
            user_id=student.id,
            user_type='student',
            priority='normal',
            icon='🎓',
            action_url=f'/app/classes/{class_obj.id}',
            action_text='View Class',
            secondary_action_url='/app/dashboard/student',
            secondary_action_text='Dashboard',
            data={'type': 'enrollment', 'class_id': class_obj.id},
            notification_type='enrollment'
        )
        
        # Create notification for professor about new enrollment
        notification_service.create_notification(
            title="New Student Enrolled 👥",
            message=f"{student.full_name} has enrolled in {class_obj.full_course_name}",
            user_id=class_obj.professor_id,
            user_type='professor',
            priority='low',
            icon='👥',
            action_url=f'/app/classes/{class_obj.id}',
            action_text='View Class',
            data={'type': 'new_enrollment', 'class_id': class_obj.id, 'student_id': student.id},
            notification_type='enrollment'
        )
    else:
        if class_obj.is_student_enrolled(student):
            flash("You are already enrolled in this class.")
        elif class_obj.is_full:
            flash("This class is full.")
        elif not class_obj.enrollment_open:
            flash("Enrollment is closed for this class.")
        else:
            flash("Unable to enroll in this class.")
    
    return redirect(url_for("classes.view_class", class_id=class_id))


@bp.route("/<int:class_id>/drop", methods=["POST"])
def drop_class(class_id):
    """Drop a class (student)"""
    auth_check = require_student()
    if auth_check:
        return auth_check
    
    student = Student.query.get(session.get("user_id"))
    class_obj = Class.query.get_or_404(class_id)
    
    if class_obj.drop_student(student):
        db.session.commit()
        flash(f"Successfully dropped {class_obj.full_course_name}.")
    else:
        flash("You are not enrolled in this class.")
    
    return redirect(url_for("classes.list_classes"))


@bp.route("/<int:class_id>/edit", methods=["GET", "POST"])
def edit_class(class_id):
    """Edit class details (professors only)"""
    auth_check = require_professor()
    if auth_check:
        return auth_check
    
    professor = Professor.query.get(session.get("user_id"))
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if professor owns this class
    if class_obj.professor_id != professor.id:
        flash("You can only edit your own classes.")
        return redirect(url_for("classes.list_classes"))
    
    if request.method == "POST":
        try:
            # Update class details
            class_obj.course_code = request.form.get("course_code", "").strip()
            class_obj.course_name = request.form.get("course_name", "").strip()
            class_obj.section = request.form.get("section", "").strip() or None
            class_obj.semester = request.form.get("semester", "").strip()
            class_obj.year = int(request.form.get("year", datetime.now().year))
            class_obj.room = request.form.get("room", "").strip() or None
            class_obj.description = request.form.get("description", "").strip() or None
            class_obj.capacity = int(request.form.get("capacity", 30))
            class_obj.credits = int(request.form.get("credits", 3))
            class_obj.meeting_days = request.form.get("meeting_days", "").strip() or None
            class_obj.enrollment_open = bool(request.form.get("enrollment_open"))
            
            # Parse times and dates
            start_time_str = request.form.get("start_time")
            end_time_str = request.form.get("end_time")
            start_date_str = request.form.get("start_date")
            end_date_str = request.form.get("end_date")
            
            class_obj.start_time = datetime.strptime(start_time_str, "%H:%M").time() if start_time_str else None
            class_obj.end_time = datetime.strptime(end_time_str, "%H:%M").time() if end_time_str else None
            class_obj.start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
            class_obj.end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
            
            class_obj.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash(f"Class '{class_obj.full_course_name}' updated successfully!")
            return redirect(url_for("classes.view_class", class_id=class_id))
            
        except ValueError as e:
            flash(f"Invalid input: {str(e)}")
        except Exception as e:
            flash(f"Error updating class: {str(e)}")
            db.session.rollback()
    
    return render_template("classes/edit_class.html", class_obj=class_obj, professor=professor)


@bp.route("/<int:class_id>/toggle_enrollment", methods=["POST"])
def toggle_enrollment(class_id):
    """Toggle enrollment status for a class"""
    auth_check = require_professor()
    if auth_check:
        return auth_check
    
    professor = Professor.query.get(session.get("user_id"))
    class_obj = Class.query.get_or_404(class_id)
    
    if class_obj.professor_id != professor.id:
        flash("You can only modify your own classes.")
        return redirect(url_for("classes.list_classes"))
    
    class_obj.enrollment_open = not class_obj.enrollment_open
    db.session.commit()
    
    status = "opened" if class_obj.enrollment_open else "closed"
    flash(f"Enrollment {status} for {class_obj.full_course_name}.")
    
    return redirect(url_for("classes.view_class", class_id=class_id))
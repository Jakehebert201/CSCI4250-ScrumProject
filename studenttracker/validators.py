"""
Input validation and sanitization utilities for security
"""
import re
import bleach
from email_validator import validate_email, EmailNotValidError


def sanitize_input(text):
    """
    Remove potentially dangerous HTML/JS from user input
    
    Args:
        text: User input string
        
    Returns:
        Sanitized string with HTML/JS removed
    """
    if not text:
        return text
    return bleach.clean(str(text), tags=[], strip=True)


def validate_email_address(email):
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        validate_email(email)
        return True, None
    except EmailNotValidError as e:
        return False, str(e)


def validate_password_strength(password):
    """
    Validate password meets security requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains number
    
    Args:
        password: Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None


def validate_username(username):
    """
    Validate username format:
    - 3-80 characters
    - Alphanumeric and underscores only
    
    Args:
        username: Username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 80:
        return False, "Username must be less than 80 characters"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, None


def validate_student_id(student_id):
    """
    Validate student ID format
    
    Args:
        student_id: Student ID to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not student_id:
        return False, "Student ID is required"
    
    if len(student_id) > 20:
        return False, "Student ID must be less than 20 characters"
    
    # Allow alphanumeric and common separators
    if not re.match(r'^[a-zA-Z0-9\-_]+$', student_id):
        return False, "Student ID contains invalid characters"
    
    return True, None


def validate_employee_id(employee_id):
    """
    Validate employee ID format
    
    Args:
        employee_id: Employee ID to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not employee_id:
        return False, "Employee ID is required"
    
    if len(employee_id) > 20:
        return False, "Employee ID must be less than 20 characters"
    
    # Allow alphanumeric and common separators
    if not re.match(r'^[a-zA-Z0-9\-_]+$', employee_id):
        return False, "Employee ID contains invalid characters"
    
    return True, None


def validate_name(name, field_name="Name"):
    """
    Validate name fields (first name, last name)
    
    Args:
        name: Name to validate
        field_name: Name of the field for error messages
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not name:
        return False, f"{field_name} is required"
    
    if len(name) > 100:
        return False, f"{field_name} must be less than 100 characters"
    
    # Allow letters, spaces, hyphens, and apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, f"{field_name} contains invalid characters"
    
    return True, None


def validate_coordinates(lat, lng):
    """
    Validate GPS coordinates
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        lat = float(lat)
        lng = float(lng)
        
        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"
        
        if not (-180 <= lng <= 180):
            return False, "Longitude must be between -180 and 180"
        
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"

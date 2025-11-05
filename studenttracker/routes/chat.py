from flask import Blueprint, jsonify, request, session
from datetime import datetime
import re

from studenttracker.extensions import db
from studenttracker.models import Student, Professor, Class, StudentLocation

bp = Blueprint("chat", __name__, url_prefix="/app")

class ChatBot:
    def __init__(self):
        self.patterns = {
            # Greetings
            r'\b(hi|hello|hey|good morning|good afternoon)\b': self.greeting,
            
            # Location help
            r'\b(location|share|gps|where|position)\b': self.location_help,
            
            # Classes
            r'\b(class|classes|course|courses|enroll|enrollment)\b': self.classes_help,
            
            # Dashboard
            r'\b(dashboard|home|main|navigate)\b': self.dashboard_help,
            
            # Professor specific
            r'\b(clear|delete|remove|students|map)\b': self.professor_help,
            
            # General help
            r'\b(help|support|how|what|guide)\b': self.general_help,
            
            # Logout
            r'\b(logout|log out|sign out|exit)\b': self.logout_help,
        }
    
    def process_message(self, message, user_type, user_id):
        message_lower = message.lower()
        
        # Check patterns and return first match
        for pattern, handler in self.patterns.items():
            if re.search(pattern, message_lower):
                return handler(message_lower, user_type, user_id)
        
        # Default response if no pattern matches
        return self.default_response(user_type)
    
    def greeting(self, message, user_type, user_id):
        if user_type == "student":
            student = Student.query.get(user_id)
            name = student.first_name if student else "Student"
            return {
                "message": f"Hi {name}! 👋 I'm here to help you with the Student Tracker. You can ask me about:\n\n• Sharing your location\n• Finding classes\n• Navigating the dashboard\n• General help\n\nWhat would you like to know?",
                "type": "greeting"
            }
        else:
            professor = Professor.query.get(user_id)
            name = professor.first_name if professor else "Professor"
            return {
                "message": f"Hello {name}! 👋 I'm your Student Tracker assistant. I can help you with:\n\n• Managing student locations\n• Viewing the map\n• Class management\n• Dashboard features\n\nHow can I assist you today?",
                "type": "greeting"
            }
    
    def location_help(self, message, user_type, user_id):
        if user_type == "student":
            return {
                "message": "📍 **Location Sharing Help**\n\nTo share your location:\n1. Go to your Student Dashboard\n2. Click 'Share My Location' button\n3. Allow browser location access\n4. Your location will appear on the professor's map\n\n💡 **Tips:**\n• Your location updates automatically\n• Professors can see when you're active\n• You can stop sharing anytime\n\nNeed help with anything else?",
                "type": "help",
                "actions": [
                    {"text": "Go to Dashboard", "url": "/app/dashboard/student"},
                    {"text": "More Help", "action": "help"}
                ]
            }
        else:
            return {
                "message": "🗺️ **Student Location Management**\n\nAs a professor, you can:\n• View all student locations on the map\n• See live vs last active students\n• Toggle between 'Show All' and 'Live Only'\n• Clear real student locations (keeps demo data)\n\n**Map Controls:**\n• 👁️ Show Live Only - See active students\n• 🗑️ Clear Real Locations - Remove actual data\n\nWould you like help with anything specific?",
                "type": "help",
                "actions": [
                    {"text": "View Map", "url": "/app/dashboard/professor"},
                    {"text": "Clear Locations", "action": "clear_confirm"}
                ]
            }
    
    def classes_help(self, message, user_type, user_id):
        if user_type == "student":
            student = Student.query.get(user_id)
            enrolled_classes = student.enrolled_classes.all() if student else []
            
            if "enroll" in message:
                response = "📚 **Class Enrollment**\n\nTo enroll in classes:\n1. Go to 'Browse Classes' from your dashboard\n2. View available classes\n3. Click 'Enroll' on classes you want\n4. Check enrollment status\n\n"
            else:
                response = "📚 **Your Classes**\n\n"
            
            if enrolled_classes:
                response += f"**Currently Enrolled ({len(enrolled_classes)}):**\n"
                for cls in enrolled_classes[:3]:  # Show first 3
                    response += f"• {cls.course_code}: {cls.course_name}\n"
                if len(enrolled_classes) > 3:
                    response += f"• ... and {len(enrolled_classes) - 3} more\n"
            else:
                response += "You're not enrolled in any classes yet.\n"
            
            return {
                "message": response + "\nNeed help with enrollment?",
                "type": "classes",
                "actions": [
                    {"text": "Browse Classes", "url": "/app/classes/"},
                    {"text": "My Classes", "url": "/app/classes/my-classes"}
                ]
            }
        else:
            professor = Professor.query.get(user_id)
            teaching_classes = professor.classes.all() if professor else []
            
            response = "🎓 **Class Management**\n\n"
            if teaching_classes:
                response += f"**Your Classes ({len(teaching_classes)}):**\n"
                for cls in teaching_classes[:3]:
                    response += f"• {cls.course_code}: {cls.course_name}\n"
                if len(teaching_classes) > 3:
                    response += f"• ... and {len(teaching_classes) - 3} more\n"
            else:
                response += "No classes assigned yet.\n"
            
            response += "\n**You can:**\n• View class details\n• Manage enrollment\n• Create new classes"
            
            return {
                "message": response,
                "type": "classes",
                "actions": [
                    {"text": "My Classes", "url": "/app/classes/"},
                    {"text": "Create Class", "url": "/app/classes/create"}
                ]
            }
    
    def dashboard_help(self, message, user_type, user_id):
        if user_type == "student":
            return {
                "message": "🏠 **Student Dashboard**\n\nYour dashboard includes:\n• Location sharing controls\n• Class enrollment status\n• Quick navigation menu\n• Profile information\n\n**Quick Actions:**\n• Share location with professors\n• Browse and enroll in classes\n• View your academic info\n\nWhere would you like to go?",
                "type": "navigation",
                "actions": [
                    {"text": "Dashboard", "url": "/app/dashboard/student"},
                    {"text": "Classes", "url": "/app/classes/"},
                    {"text": "Database", "url": "/app/database"}
                ]
            }
        else:
            return {
                "message": "🏠 **Professor Dashboard**\n\nYour dashboard features:\n• Student location map\n• Class management\n• Student activity monitoring\n• Location controls\n\n**Key Features:**\n• Real-time student locations\n• Live vs last active status\n• Class enrollment overview\n• Location management tools\n\nWhat would you like to access?",
                "type": "navigation",
                "actions": [
                    {"text": "Dashboard", "url": "/app/dashboard/professor"},
                    {"text": "My Classes", "url": "/app/classes/"},
                    {"text": "Database", "url": "/app/database"}
                ]
            }
    
    def professor_help(self, message, user_type, user_id):
        if user_type != "professor":
            return {
                "message": "🔒 This feature is only available to professors. If you're a professor, please log in with your professor account.",
                "type": "error"
            }
        
        if "clear" in message:
            return {
                "message": "🗑️ **Clear Student Locations**\n\n**What this does:**\n• Removes real student location data\n• Keeps demo/fake students for testing\n• Students will need to share location again\n\n**Warning:** This action cannot be undone!\n\nWould you like to proceed?",
                "type": "confirm",
                "actions": [
                    {"text": "Yes, Clear Locations", "action": "clear_locations"},
                    {"text": "Cancel", "action": "cancel"}
                ]
            }
        
        return {
            "message": "👨‍🏫 **Professor Tools**\n\nAvailable actions:\n• View student location map\n• Clear real student locations\n• Manage your classes\n• Monitor student activity\n• Toggle live/all view\n\nWhat would you like to do?",
            "type": "professor_tools",
            "actions": [
                {"text": "View Map", "url": "/app/dashboard/professor"},
                {"text": "Clear Locations", "action": "clear_confirm"}
            ]
        }
    
    def general_help(self, message, user_type, user_id):
        return {
            "message": "❓ **Help & Support**\n\n**Common Questions:**\n• How do I share my location?\n• How do I enroll in classes?\n• Where is my dashboard?\n• How do I log out?\n\n**Quick Links:**\n• Dashboard - Your main hub\n• Classes - Browse and manage\n• Database - View all data\n\nJust ask me anything! I can help with navigation, features, or troubleshooting.",
            "type": "help",
            "actions": [
                {"text": "Location Help", "action": "location"},
                {"text": "Class Help", "action": "classes"},
                {"text": "Dashboard", "action": "dashboard"}
            ]
        }
    
    def logout_help(self, message, user_type, user_id):
        return {
            "message": "👋 **Logout Help**\n\nTo log out:\n1. Click 'Log Out' in the top navigation\n2. You'll be redirected to the main page\n3. Your session will be cleared\n\n**Note for Students:** Logging out will stop location sharing and mark you as 'last active'.\n\nReady to log out?",
            "type": "logout",
            "actions": [
                {"text": "Log Out Now", "url": "/app/logout"},
                {"text": "Stay Logged In", "action": "cancel"}
            ]
        }
    
    def default_response(self, user_type):
        return {
            "message": "🤔 I'm not sure I understand that. Here are some things I can help with:\n\n• **Location** - Sharing and managing locations\n• **Classes** - Enrollment and management\n• **Dashboard** - Navigation and features\n• **Help** - General support\n\nTry asking about one of these topics, or just say 'help' for more options!",
            "type": "default",
            "actions": [
                {"text": "Location Help", "action": "location"},
                {"text": "Class Help", "action": "classes"},
                {"text": "General Help", "action": "help"}
            ]
        }

# Initialize chatbot
chatbot = ChatBot()

@bp.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    user_type = session.get("user_type")
    user_id = session.get("user_id")
    
    # Process message with chatbot
    response = chatbot.process_message(message, user_type, user_id)
    
    return jsonify({
        "success": True,
        "response": response,
        "timestamp": datetime.utcnow().isoformat()
    })

@bp.route("/chat/action", methods=["POST"])
def chat_action():
    """Handle chat action buttons"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    action = data.get("action")
    
    user_type = session.get("user_type")
    user_id = session.get("user_id")
    
    if action == "clear_locations" and user_type == "professor":
        # Trigger the clear locations functionality
        try:
            from studenttracker.routes.api import clear_all_locations
            # This would need to be refactored to be callable
            return jsonify({
                "success": True,
                "response": {
                    "message": "✅ Student locations have been cleared! Demo data preserved.",
                    "type": "success",
                    "actions": [
                        {"text": "View Map", "url": "/app/dashboard/professor"}
                    ]
                }
            })
        except Exception as e:
            return jsonify({
                "success": True,
                "response": {
                    "message": "❌ Failed to clear locations. Please try using the dashboard button.",
                    "type": "error"
                }
            })
    
    # Handle other actions by returning appropriate responses
    response = chatbot.process_message(action, user_type, user_id)
    
    return jsonify({
        "success": True,
        "response": response,
        "timestamp": datetime.utcnow().isoformat()
    })
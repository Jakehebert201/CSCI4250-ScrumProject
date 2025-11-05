from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for
from datetime import datetime

from studenttracker.extensions import db
from studenttracker.models import (
    Notification, NotificationType, UserNotificationPreference, PushSubscription
)
from studenttracker.services.notification_service import notification_service

bp = Blueprint("notifications", __name__, url_prefix="/app")

@bp.route("/notifications")
def notification_center():
    """Notification center page"""
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    
    return render_template("notifications/center.html")

@bp.route("/api/notifications")
def get_notifications():
    """Get user's notifications"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get("user_id")
    user_type = session.get("user_type")
    
    # Get query parameters
    limit = min(int(request.args.get("limit", 20)), 50)
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    
    # Get notifications
    notifications = notification_service.get_user_notifications(
        user_id=user_id,
        user_type=user_type,
        limit=limit,
        unread_only=unread_only
    )
    
    # Convert to dict
    notifications_data = [notif.to_dict() for notif in notifications]
    
    # Get unread count
    unread_count = len(notification_service.get_user_notifications(
        user_id=user_id,
        user_type=user_type,
        limit=100,
        unread_only=True
    ))
    
    return jsonify({
        "success": True,
        "notifications": notifications_data,
        "unread_count": unread_count,
        "total_count": len(notifications_data)
    })

@bp.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get("user_id")
    success = notification_service.mark_notification_read(notification_id, user_id)
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Notification not found or access denied"}), 404

@bp.route("/api/notifications/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get("user_id")
    user_type = session.get("user_type")
    
    try:
        # Get all unread notifications for user
        notifications = notification_service.get_user_notifications(
            user_id=user_id,
            user_type=user_type,
            limit=100,
            unread_only=True
        )
        
        # Mark all as read
        for notification in notifications:
            notification.mark_as_read()
        
        return jsonify({"success": True, "marked_count": len(notifications)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/api/notifications/preferences")
def get_notification_preferences():
    """Get user's notification preferences"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get("user_id")
    user_type = session.get("user_type")
    
    prefs = notification_service._get_user_preferences(user_id, user_type)
    
    return jsonify({
        "success": True,
        "preferences": {
            "browser_push_enabled": prefs.browser_push_enabled,
            "email_enabled": prefs.email_enabled,
            "in_app_enabled": prefs.in_app_enabled,
            "class_reminders_enabled": prefs.class_reminders_enabled,
            "class_reminder_minutes": prefs.class_reminder_minutes,
            "location_alerts_enabled": prefs.location_alerts_enabled,
            "attendance_alerts_enabled": prefs.attendance_alerts_enabled,
            "emergency_notifications_enabled": prefs.emergency_notifications_enabled,
            "digest_frequency": prefs.digest_frequency,
            "quiet_hours_start": prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
            "quiet_hours_end": prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None
        }
    })

@bp.route("/api/notifications/preferences", methods=["POST"])
def update_notification_preferences():
    """Update user's notification preferences"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get("user_id")
    user_type = session.get("user_type")
    
    try:
        data = request.get_json()
        prefs = notification_service._get_user_preferences(user_id, user_type)
        
        # Update preferences
        if "browser_push_enabled" in data:
            prefs.browser_push_enabled = data["browser_push_enabled"]
        if "email_enabled" in data:
            prefs.email_enabled = data["email_enabled"]
        if "in_app_enabled" in data:
            prefs.in_app_enabled = data["in_app_enabled"]
        if "class_reminders_enabled" in data:
            prefs.class_reminders_enabled = data["class_reminders_enabled"]
        if "class_reminder_minutes" in data:
            prefs.class_reminder_minutes = data["class_reminder_minutes"]
        if "location_alerts_enabled" in data:
            prefs.location_alerts_enabled = data["location_alerts_enabled"]
        if "attendance_alerts_enabled" in data:
            prefs.attendance_alerts_enabled = data["attendance_alerts_enabled"]
        if "emergency_notifications_enabled" in data:
            prefs.emergency_notifications_enabled = data["emergency_notifications_enabled"]
        if "digest_frequency" in data:
            prefs.digest_frequency = data["digest_frequency"]
        
        # Handle quiet hours
        if "quiet_hours_start" in data and data["quiet_hours_start"]:
            prefs.quiet_hours_start = datetime.strptime(data["quiet_hours_start"], "%H:%M").time()
        if "quiet_hours_end" in data and data["quiet_hours_end"]:
            prefs.quiet_hours_end = datetime.strptime(data["quiet_hours_end"], "%H:%M").time()
        
        db.session.commit()
        
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route("/api/notifications/push/subscribe", methods=["POST"])
def subscribe_to_push():
    """Subscribe to browser push notifications"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get("user_id")
    user_type = session.get("user_type")
    
    try:
        data = request.get_json()
        
        # Extract subscription data
        subscription_data = data.get("subscription", {})
        endpoint = subscription_data.get("endpoint")
        keys = subscription_data.get("keys", {})
        p256dh_key = keys.get("p256dh")
        auth_key = keys.get("auth")
        
        if not all([endpoint, p256dh_key, auth_key]):
            return jsonify({"error": "Invalid subscription data"}), 400
        
        # Check if subscription already exists
        existing = PushSubscription.query.filter_by(
            user_id=user_id,
            user_type=user_type,
            endpoint=endpoint
        ).first()
        
        if existing:
            # Update existing subscription
            existing.p256dh_key = p256dh_key
            existing.auth_key = auth_key
            existing.is_active = True
            existing.last_used = datetime.utcnow()
        else:
            # Create new subscription
            subscription = PushSubscription(
                user_id=user_id,
                user_type=user_type,
                endpoint=endpoint,
                p256dh_key=p256dh_key,
                auth_key=auth_key,
                user_agent=request.headers.get("User-Agent", ""),
                browser=data.get("browser", "unknown"),
                device_type=data.get("device_type", "unknown")
            )
            db.session.add(subscription)
        
        db.session.commit()
        
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route("/api/notifications/push/unsubscribe", methods=["POST"])
def unsubscribe_from_push():
    """Unsubscribe from browser push notifications"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get("user_id")
    user_type = session.get("user_type")
    
    try:
        data = request.get_json()
        endpoint = data.get("endpoint")
        
        if endpoint:
            # Deactivate specific subscription
            subscription = PushSubscription.query.filter_by(
                user_id=user_id,
                user_type=user_type,
                endpoint=endpoint
            ).first()
            
            if subscription:
                subscription.is_active = False
                db.session.commit()
        else:
            # Deactivate all subscriptions for user
            PushSubscription.query.filter_by(
                user_id=user_id,
                user_type=user_type
            ).update({"is_active": False})
            db.session.commit()
        
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route("/api/notifications/test", methods=["POST"])
def send_test_notification():
    """Send a test notification (for development)"""
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get("user_id")
    user_type = session.get("user_type")
    
    try:
        # Create test notification
        notification = notification_service.create_notification(
            title="Test Notification 🧪",
            message="This is a test notification to verify the system is working correctly!",
            user_id=user_id,
            user_type=user_type,
            priority="normal",
            icon="🧪",
            action_url="/app/notifications",
            action_text="View Notifications",
            data={"type": "test"}
        )
        
        return jsonify({
            "success": True,
            "notification_id": notification.id,
            "message": "Test notification sent!"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Admin routes (for professors/testing)
@bp.route("/api/notifications/broadcast", methods=["POST"])
def broadcast_notification():
    """Send broadcast notification (professors only)"""
    if not session.get("user_id") or session.get("user_type") != "professor":
        return jsonify({"error": "Access denied"}), 403
    
    try:
        data = request.get_json()
        
        notification = notification_service.create_notification(
            title=data.get("title", "Campus Announcement"),
            message=data.get("message", ""),
            user_type=data.get("target_type"),  # 'student', 'professor', or None for all
            priority=data.get("priority", "normal"),
            icon=data.get("icon", "📢"),
            action_url=data.get("action_url"),
            action_text=data.get("action_text"),
            data={"type": "broadcast", "sender_id": session.get("user_id")}
        )
        
        return jsonify({
            "success": True,
            "notification_id": notification.id,
            "message": "Broadcast notification sent!"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
import json
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from studenttracker.extensions import db
from studenttracker.models import (
    Student, Professor, Class, Notification, NotificationType, 
    UserNotificationPreference, PushSubscription
)

class NotificationService:
    def __init__(self):
        self.vapid_private_key = None  # Will be set from environment
        self.vapid_public_key = None
        self.vapid_email = None
    
    def create_notification(
        self,
        title: str,
        message: str,
        user_id: Optional[int] = None,
        user_type: Optional[str] = None,
        priority: str = 'normal',
        icon: str = '🔔',
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        secondary_action_url: Optional[str] = None,
        secondary_action_text: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        scheduled_for: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        notification_type: Optional[str] = None
    ) -> Notification:
        """Create a new notification"""
        
        # Get notification type if specified
        type_obj = None
        if notification_type:
            type_obj = NotificationType.query.filter_by(name=notification_type).first()
        
        notification = Notification(
            title=title,
            message=message,
            user_id=user_id,
            user_type=user_type,
            priority=priority,
            icon=icon,
            action_url=action_url,
            action_text=action_text,
            secondary_action_url=secondary_action_url,
            secondary_action_text=secondary_action_text,
            data=data or {},
            scheduled_for=scheduled_for,
            expires_at=expires_at,
            type_id=type_obj.id if type_obj else None
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Send immediately if not scheduled
        if not scheduled_for or scheduled_for <= datetime.utcnow():
            self.send_notification(notification)
        
        return notification
    
    def send_notification(self, notification: Notification) -> bool:
        """Send a notification via all enabled channels"""
        try:
            # Mark as sent
            notification.is_sent = True
            notification.sent_at = datetime.utcnow()
            
            # Get recipients
            recipients = self._get_recipients(notification)
            
            success = True
            for recipient in recipients:
                # Check user preferences
                prefs = self._get_user_preferences(recipient['user_id'], recipient['user_type'])
                
                # Skip if in quiet hours
                if self._is_quiet_hours(prefs):
                    continue
                
                # Send via enabled channels
                if prefs.browser_push_enabled:
                    success &= self._send_push_notification(notification, recipient)
                
                if prefs.in_app_enabled:
                    # In-app notifications are stored in DB, no additional action needed
                    pass
            
            db.session.commit()
            return success
            
        except Exception as e:
            print(f"Error sending notification: {e}")
            db.session.rollback()
            return False
    
    def _get_recipients(self, notification: Notification) -> List[Dict[str, Any]]:
        """Get list of recipients for a notification"""
        recipients = []
        
        if notification.user_id:
            # Specific user
            recipients.append({
                'user_id': notification.user_id,
                'user_type': notification.user_type or 'student'
            })
        elif notification.user_type:
            # All users of a specific type
            if notification.user_type == 'student':
                students = Student.query.all()
                recipients.extend([
                    {'user_id': s.id, 'user_type': 'student'} for s in students
                ])
            elif notification.user_type == 'professor':
                professors = Professor.query.all()
                recipients.extend([
                    {'user_id': p.id, 'user_type': 'professor'} for p in professors
                ])
        else:
            # Broadcast to all users
            students = Student.query.all()
            professors = Professor.query.all()
            recipients.extend([
                {'user_id': s.id, 'user_type': 'student'} for s in students
            ])
            recipients.extend([
                {'user_id': p.id, 'user_type': 'professor'} for p in professors
            ])
        
        return recipients
    
    def _get_user_preferences(self, user_id: int, user_type: str) -> UserNotificationPreference:
        """Get user notification preferences, create default if not exists"""
        prefs = UserNotificationPreference.query.filter_by(
            user_id=user_id, user_type=user_type
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = UserNotificationPreference(
                user_id=user_id,
                user_type=user_type
            )
            db.session.add(prefs)
            db.session.commit()
        
        return prefs
    
    def _is_quiet_hours(self, prefs: UserNotificationPreference) -> bool:
        """Check if current time is within user's quiet hours"""
        if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False
        
        now = datetime.now().time()
        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end
        
        # Handle overnight quiet hours (e.g., 22:00 to 07:00)
        if start > end:
            return now >= start or now <= end
        else:
            return start <= now <= end
    
    def _send_push_notification(self, notification: Notification, recipient: Dict[str, Any]) -> bool:
        """Send browser push notification"""
        try:
            # Get user's push subscriptions
            subscriptions = PushSubscription.query.filter_by(
                user_id=recipient['user_id'],
                user_type=recipient['user_type'],
                is_active=True
            ).all()
            
            if not subscriptions:
                return True  # No subscriptions, but not an error
            
            # Prepare push payload
            payload = {
                'title': notification.title,
                'body': notification.message,
                'icon': '/static/icons/notification-icon.png',
                'badge': '/static/icons/badge-icon.png',
                'tag': f'notification-{notification.id}',
                'data': {
                    'notification_id': notification.id,
                    'action_url': notification.action_url,
                    'priority': notification.priority
                },
                'actions': []
            }
            
            # Add action buttons
            if notification.action_url and notification.action_text:
                payload['actions'].append({
                    'action': 'open',
                    'title': notification.action_text,
                    'url': notification.action_url
                })
            
            if notification.secondary_action_url and notification.secondary_action_text:
                payload['actions'].append({
                    'action': 'secondary',
                    'title': notification.secondary_action_text,
                    'url': notification.secondary_action_url
                })
            
            # Send to each subscription
            success = True
            for subscription in subscriptions:
                try:
                    # Here you would use a library like pywebpush to send the notification
                    # For now, we'll just log it
                    print(f"Sending push notification to user {recipient['user_id']}: {notification.title}")
                    # self._send_webpush(subscription, payload)
                except Exception as e:
                    print(f"Failed to send push to subscription {subscription.id}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            print(f"Error sending push notification: {e}")
            return False
    
    def get_user_notifications(
        self, 
        user_id: int, 
        user_type: str, 
        limit: int = 20, 
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a specific user"""
        query = Notification.query.filter(
            db.or_(
                Notification.user_id == user_id,
                Notification.user_type == user_type,
                db.and_(Notification.user_id.is_(None), Notification.user_type.is_(None))
            )
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        # Filter out expired notifications
        query = query.filter(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read for a specific user"""
        try:
            notification = Notification.query.get(notification_id)
            if notification and (
                notification.user_id == user_id or 
                notification.user_id is None
            ):
                notification.mark_as_read()
                return True
            return False
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    def create_class_reminder(self, class_obj: Class, minutes_before: int = 15):
        """Create a class reminder notification"""
        # Calculate notification time
        if not class_obj.start_time:
            return None
        
        # For now, we'll use today's date + class time
        # In a real app, you'd have proper class scheduling
        today = datetime.now().date()
        class_datetime = datetime.combine(today, class_obj.start_time)
        notification_time = class_datetime - timedelta(minutes=minutes_before)
        
        # Only create if notification time is in the future
        if notification_time <= datetime.now():
            return None
        
        # Get enrolled students
        enrolled_students = class_obj.enrolled_students.all()
        
        for student in enrolled_students:
            self.create_notification(
                title=f"Class Starting Soon! 📚",
                message=f"{class_obj.course_code} starts in {minutes_before} minutes\nRoom: {class_obj.room or 'TBD'}",
                user_id=student.id,
                user_type='student',
                priority='normal',
                icon='📚',
                action_url='/app/dashboard/student',
                action_text='Share Location',
                secondary_action_url=f'/app/classes/{class_obj.id}',
                secondary_action_text='View Class',
                data={
                    'class_id': class_obj.id,
                    'type': 'class_reminder'
                },
                scheduled_for=notification_time,
                expires_at=class_datetime + timedelta(hours=1),
                notification_type='class_reminder'
            )
    
    def create_attendance_alert(self, class_obj: Class, attendance_count: int, total_enrolled: int):
        """Create low attendance alert for professor"""
        if total_enrolled == 0:
            return None
        
        attendance_rate = (attendance_count / total_enrolled) * 100
        
        if attendance_rate < 50:  # Alert if less than 50% attendance
            self.create_notification(
                title=f"Low Attendance Alert ⚠️",
                message=f"Only {attendance_count}/{total_enrolled} students ({attendance_rate:.0f}%) have checked in to {class_obj.course_code}",
                user_id=class_obj.professor_id,
                user_type='professor',
                priority='high',
                icon='⚠️',
                action_url='/app/dashboard/professor',
                action_text='View Map',
                secondary_action_url=f'/app/classes/{class_obj.id}',
                secondary_action_text='View Class',
                data={
                    'class_id': class_obj.id,
                    'attendance_count': attendance_count,
                    'total_enrolled': total_enrolled,
                    'attendance_rate': attendance_rate,
                    'type': 'attendance_alert'
                },
                expires_at=datetime.utcnow() + timedelta(hours=2),
                notification_type='attendance_alert'
            )
    
    def create_location_alert(self, student_id: int, message: str, priority: str = 'normal'):
        """Create location-based alert"""
        student = Student.query.get(student_id)
        if not student:
            return None
        
        self.create_notification(
            title=f"Location Update 📍",
            message=message,
            user_id=student_id,
            user_type='student',
            priority=priority,
            icon='📍',
            action_url='/app/dashboard/student',
            action_text='Update Location',
            data={
                'student_id': student_id,
                'type': 'location_alert'
            },
            expires_at=datetime.utcnow() + timedelta(hours=4),
            notification_type='location_alert'
        )
    
    def create_emergency_alert(self, title: str, message: str, action_url: str = None):
        """Create emergency notification for all users"""
        self.create_notification(
            title=f"🚨 {title}",
            message=message,
            user_id=None,  # Broadcast to all
            user_type=None,
            priority='urgent',
            icon='🚨',
            action_url=action_url or '/app/dashboard',
            action_text='View Details',
            data={
                'type': 'emergency'
            },
            expires_at=datetime.utcnow() + timedelta(hours=24),
            notification_type='emergency'
        )

# Global notification service instance
notification_service = NotificationService()
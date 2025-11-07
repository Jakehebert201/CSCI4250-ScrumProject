class NotificationManager {
    constructor() {
        this.notifications = [];
        this.currentFilter = 'all';
        this.pushSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadNotifications();
        this.setupPushNotifications();
        this.startPolling();
    }

    bindEvents() {
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter(e.target.dataset.filter);
            });
        });

        // Control buttons
        document.getElementById('mark-all-read-btn')?.addEventListener('click', () => {
            this.markAllAsRead();
        });

        document.getElementById('preferences-btn')?.addEventListener('click', () => {
            this.openPreferences();
        });

        document.getElementById('broadcast-btn')?.addEventListener('click', () => {
            this.openBroadcast();
        });

        document.getElementById('test-notification-btn')?.addEventListener('click', () => {
            this.sendTestNotification();
        });

        document.getElementById('cleanup-btn')?.addEventListener('click', () => {
            this.cleanupNotifications();
        });

        // Modal events
        this.bindModalEvents();
    }

    bindModalEvents() {
        // Preferences modal
        const prefsModal = document.getElementById('preferences-modal');
        const prefsClose = document.getElementById('preferences-close');
        const prefsCancel = document.getElementById('preferences-cancel');
        const prefsSave = document.getElementById('preferences-save');

        [prefsClose, prefsCancel].forEach(btn => {
            btn?.addEventListener('click', () => {
                prefsModal.classList.remove('open');
            });
        });

        prefsSave?.addEventListener('click', () => {
            this.savePreferences();
        });

        // Broadcast modal
        const broadcastModal = document.getElementById('broadcast-modal');
        const broadcastClose = document.getElementById('broadcast-close');
        const broadcastCancel = document.getElementById('broadcast-cancel');
        const broadcastSend = document.getElementById('broadcast-send');

        [broadcastClose, broadcastCancel].forEach(btn => {
            btn?.addEventListener('click', () => {
                broadcastModal.classList.remove('open');
            });
        });

        broadcastSend?.addEventListener('click', () => {
            this.sendBroadcast();
        });

        // Close modals on backdrop click
        [prefsModal, broadcastModal].forEach(modal => {
            modal?.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('open');
                }
            });
        });
    }

    async loadNotifications() {
        try {
            this.showLoading(true);
            
            const response = await fetch('/app/api/notifications', {
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.notifications = data.notifications;
                this.updateNotificationCount(data.unread_count);
                this.renderNotifications();
            } else {
                this.showError('Failed to load notifications');
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError('Failed to load notifications');
        } finally {
            this.showLoading(false);
        }
    }

    renderNotifications() {
        const container = document.getElementById('notification-list');
        const emptyState = document.getElementById('notification-empty');
        
        // Filter notifications
        const filteredNotifications = this.filterNotifications();
        
        if (filteredNotifications.length === 0) {
            container.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }
        
        emptyState.style.display = 'none';
        
        container.innerHTML = filteredNotifications.map(notification => 
            this.createNotificationHTML(notification)
        ).join('');
        
        // Bind notification events
        this.bindNotificationEvents();
    }

    createNotificationHTML(notification) {
        const timeAgo = this.getTimeAgo(new Date(notification.created_at));
        const priorityClass = notification.priority !== 'normal' ? `priority-${notification.priority}` : '';
        const unreadClass = !notification.is_read ? 'unread' : '';
        
        return `
            <div class="notification-item ${unreadClass} ${priorityClass}" data-id="${notification.id}">
                <button class="notification-close" data-notification-id="${notification.id}" title="Remove notification">×</button>
                <div class="notification-content">
                    <div class="notification-icon" style="background: ${notification.priority_color}20;">
                        ${notification.priority_icon}
                    </div>
                    <div class="notification-body">
                        <h3 class="notification-title-text">${this.escapeHtml(notification.title)}</h3>
                        <p class="notification-message">${this.escapeHtml(notification.message)}</p>
                        <div class="notification-meta">
                            <span class="notification-time">${timeAgo}</span>
                            <div class="notification-actions">
                                ${notification.action_url ? `
                                    <a href="${notification.action_url}" class="notification-action primary">
                                        ${notification.action_text || 'View'}
                                    </a>
                                ` : ''}
                                ${notification.secondary_action_url ? `
                                    <a href="${notification.secondary_action_url}" class="notification-action">
                                        ${notification.secondary_action_text || 'More'}
                                    </a>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    bindNotificationEvents() {
        // Delete button clicks
        document.querySelectorAll('.notification-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationId = parseInt(btn.dataset.notificationId);
                this.deleteNotification(notificationId);
            });
        });
        
        // Click to mark as read
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.notification-action') && !e.target.closest('.notification-close')) {
                    const id = parseInt(item.dataset.id);
                    this.markAsRead(id);
                }
            });
        });
    }

    filterNotifications() {
        switch (this.currentFilter) {
            case 'unread':
                return this.notifications.filter(n => !n.is_read);
            case 'class':
                return this.notifications.filter(n => 
                    n.data?.type === 'class_reminder' || 
                    n.title.toLowerCase().includes('class')
                );
            case 'location':
                return this.notifications.filter(n => 
                    n.data?.type === 'location_alert' || 
                    n.title.toLowerCase().includes('location')
                );
            case 'emergency':
                return this.notifications.filter(n => 
                    n.priority === 'urgent' || 
                    n.data?.type === 'emergency'
                );
            default:
                return this.notifications;
        }
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update active filter button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        this.renderNotifications();
    }

    async markAsRead(notificationId, remove = false) {
        try {
            const response = await fetch(`/app/api/notifications/${notificationId}/read`, {
                method: 'POST',
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                if (remove) {
                    // Remove from local state
                    this.notifications = this.notifications.filter(n => n.id !== notificationId);
                } else {
                    // Update local state
                    const notification = this.notifications.find(n => n.id === notificationId);
                    if (notification) {
                        notification.is_read = true;
                    }
                }
                
                this.updateNotificationCount();
                this.renderNotifications();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async deleteNotification(notificationId) {
        try {
            // Try DELETE method first, fallback to POST
            let response = await fetch(`/app/api/notifications/${notificationId}`, {
                method: 'DELETE',
                credentials: 'same-origin'
            });
            
            // If DELETE fails, try POST
            if (!response.ok && response.status === 405) {
                response = await fetch(`/app/api/notifications/${notificationId}`, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ _method: 'DELETE' })
                });
            }
            
            if (response.ok) {
                const result = await response.json();
                console.log('Delete successful:', result);
                
                // Remove from local state
                this.notifications = this.notifications.filter(n => n.id !== notificationId);
                this.updateNotificationCount();
                this.renderNotifications();
                
                // Show subtle feedback
                this.showToast('Notification removed', 'success');
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('Delete failed:', response.status, errorData);
                this.showError(errorData.error || `Failed to delete notification (${response.status})`);
            }
        } catch (error) {
            console.error('Error deleting notification:', error);
            this.showError('Failed to delete notification: ' + error.message);
        }
    }

    async markAllAsRead() {
        try {
            const response = await fetch('/app/api/notifications/mark-all-read', {
                method: 'POST',
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update local state
                this.notifications.forEach(n => n.is_read = true);
                this.updateNotificationCount();
                this.renderNotifications();
                this.showToast('All notifications marked as read', 'success');
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
            this.showError('Failed to mark notifications as read');
        }
    }

    async openPreferences() {
        try {
            // Load current preferences
            const response = await fetch('/app/api/notifications/preferences', {
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.populatePreferences(data.preferences);
                document.getElementById('preferences-modal').classList.add('open');
            }
        } catch (error) {
            console.error('Error loading preferences:', error);
            this.showError('Failed to load preferences');
        }
    }

    populatePreferences(prefs) {
        document.getElementById('browser-push-enabled').checked = prefs.browser_push_enabled;
        document.getElementById('in-app-enabled').checked = prefs.in_app_enabled;
        document.getElementById('email-enabled').checked = prefs.email_enabled;
        document.getElementById('class-reminders-enabled').checked = prefs.class_reminders_enabled;
        document.getElementById('class-reminder-minutes').value = prefs.class_reminder_minutes;
        document.getElementById('location-alerts-enabled').checked = prefs.location_alerts_enabled;
        
        const attendanceCheckbox = document.getElementById('attendance-alerts-enabled');
        if (attendanceCheckbox) {
            attendanceCheckbox.checked = prefs.attendance_alerts_enabled;
        }
        
        document.getElementById('emergency-notifications-enabled').checked = prefs.emergency_notifications_enabled;
        
        if (prefs.quiet_hours_start) {
            document.getElementById('quiet-hours-start').value = prefs.quiet_hours_start;
        }
        if (prefs.quiet_hours_end) {
            document.getElementById('quiet-hours-end').value = prefs.quiet_hours_end;
        }
    }

    async savePreferences() {
        try {
            const preferences = {
                browser_push_enabled: document.getElementById('browser-push-enabled').checked,
                in_app_enabled: document.getElementById('in-app-enabled').checked,
                email_enabled: document.getElementById('email-enabled').checked,
                class_reminders_enabled: document.getElementById('class-reminders-enabled').checked,
                class_reminder_minutes: parseInt(document.getElementById('class-reminder-minutes').value),
                location_alerts_enabled: document.getElementById('location-alerts-enabled').checked,
                emergency_notifications_enabled: document.getElementById('emergency-notifications-enabled').checked,
                quiet_hours_start: document.getElementById('quiet-hours-start').value || null,
                quiet_hours_end: document.getElementById('quiet-hours-end').value || null
            };
            
            const attendanceCheckbox = document.getElementById('attendance-alerts-enabled');
            if (attendanceCheckbox) {
                preferences.attendance_alerts_enabled = attendanceCheckbox.checked;
            }
            
            const response = await fetch('/app/api/notifications/preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify(preferences)
            });
            
            if (response.ok) {
                document.getElementById('preferences-modal').classList.remove('open');
                this.showToast('Preferences saved successfully', 'success');
                
                // Update push subscription if needed
                if (preferences.browser_push_enabled) {
                    this.subscribeToPush();
                } else {
                    this.unsubscribeFromPush();
                }
            } else {
                this.showError('Failed to save preferences');
            }
        } catch (error) {
            console.error('Error saving preferences:', error);
            this.showError('Failed to save preferences');
        }
    }

    openBroadcast() {
        document.getElementById('broadcast-modal').classList.add('open');
    }

    async sendBroadcast() {
        try {
            const title = document.getElementById('broadcast-title').value;
            const message = document.getElementById('broadcast-message').value;
            const target = document.getElementById('broadcast-target').value;
            const priority = document.getElementById('broadcast-priority').value;
            
            if (!title || !message) {
                this.showError('Please fill in all required fields');
                return;
            }
            
            const response = await fetch('/app/api/notifications/broadcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    title,
                    message,
                    target_type: target || null,
                    priority
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('broadcast-modal').classList.remove('open');
                document.getElementById('broadcast-form').reset();
                this.showToast('Broadcast sent successfully', 'success');
                this.loadNotifications(); // Refresh to show new notification
            } else {
                this.showError(data.error || 'Failed to send broadcast');
            }
        } catch (error) {
            console.error('Error sending broadcast:', error);
            this.showError('Failed to send broadcast');
        }
    }

    async sendTestNotification() {
        try {
            const response = await fetch('/app/api/notifications/test', {
                method: 'POST',
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Test notification sent!', 'success');
                setTimeout(() => this.loadNotifications(), 1000);
            } else {
                this.showError(data.error || 'Failed to send test notification');
            }
        } catch (error) {
            console.error('Error sending test notification:', error);
            this.showError('Failed to send test notification');
        }
    }

    async cleanupNotifications() {
        // Ask user which mode
        const mode = confirm('Choose cleanup mode:\n\nOK = Aggressive (delete ALL read notifications)\nCancel = Standard (only old notifications)');
        
        const aggressive = mode; // true if OK clicked
        
        const confirmMsg = aggressive 
            ? 'AGGRESSIVE MODE:\n• All expired notifications\n• ALL read notifications\n• ALL low-priority notifications\n\nThis will delete most of your notifications!\n\nContinue?'
            : 'STANDARD MODE:\n• Expired notifications\n• Read notifications older than 30 days\n• Unread low-priority notifications older than 7 days\n\nContinue?';
        
        if (!confirm(confirmMsg)) {
            return;
        }

        try {
            const response = await fetch('/app/api/notifications/cleanup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ aggressive })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const total = data.deleted.total;
                const details = `Deleted: ${data.deleted.expired} expired, ${data.deleted.old_read} read, ${data.deleted.old_low_priority} low-priority`;
                this.showToast(`Cleaned up ${total} notification${total !== 1 ? 's' : ''} (${data.mode} mode)`, 'success');
                
                // Force reload notifications from server
                await this.loadNotifications();
            } else {
                this.showError(data.error || 'Failed to cleanup notifications');
            }
        } catch (error) {
            console.error('Error cleaning up notifications:', error);
            this.showError('Failed to cleanup notifications');
        }
    }

    async setupPushNotifications() {
        if (!this.pushSupported) {
            console.log('Push notifications not supported');
            return;
        }

        try {
            // Register service worker
            const registration = await navigator.serviceWorker.register('/static/js/sw.js');
            console.log('Service Worker registered:', registration);
            
            // Check if already subscribed
            const subscription = await registration.pushManager.getSubscription();
            if (subscription) {
                console.log('Already subscribed to push notifications');
            }
        } catch (error) {
            console.error('Error setting up push notifications:', error);
        }
    }

    async subscribeToPush() {
        if (!this.pushSupported) return;

        try {
            const registration = await navigator.serviceWorker.ready;
            
            // Request permission
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                this.showError('Notification permission denied');
                return;
            }
            
            // Subscribe to push
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array('your-vapid-public-key-here')
            });
            
            // Send subscription to server
            await fetch('/app/api/notifications/push/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    subscription: subscription.toJSON(),
                    browser: this.getBrowserInfo(),
                    device_type: this.getDeviceType()
                })
            });
            
            console.log('Subscribed to push notifications');
        } catch (error) {
            console.error('Error subscribing to push:', error);
        }
    }

    async unsubscribeFromPush() {
        if (!this.pushSupported) return;

        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            if (subscription) {
                await subscription.unsubscribe();
                
                // Notify server
                await fetch('/app/api/notifications/push/unsubscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        endpoint: subscription.endpoint
                    })
                });
            }
        } catch (error) {
            console.error('Error unsubscribing from push:', error);
        }
    }

    startPolling() {
        // Poll for new notifications every 30 seconds
        setInterval(() => {
            this.loadNotifications();
        }, 30000);
    }

    updateNotificationCount(count = null) {
        if (count === null) {
            count = this.notifications.filter(n => !n.is_read).length;
        }
        
        const countElement = document.getElementById('notification-count');
        if (countElement) {
            countElement.textContent = count;
            countElement.style.display = count > 0 ? 'block' : 'none';
        }
    }

    showLoading(show) {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.style.display = show ? 'flex' : 'none';
        }
    }

    showToast(message, type = 'success') {
        const container = this.getToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    getToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    getBrowserInfo() {
        const ua = navigator.userAgent;
        if (ua.includes('Chrome')) return 'Chrome';
        if (ua.includes('Firefox')) return 'Firefox';
        if (ua.includes('Safari')) return 'Safari';
        if (ua.includes('Edge')) return 'Edge';
        return 'Unknown';
    }

    getDeviceType() {
        const ua = navigator.userAgent;
        if (/tablet|ipad|playbook|silk/i.test(ua)) return 'tablet';
        if (/mobile|iphone|ipod|android|blackberry|opera|mini|windows\sce|palm|smartphone|iemobile/i.test(ua)) return 'mobile';
        return 'desktop';
    }
}

// Initialize notification manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});
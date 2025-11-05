// Notification Badge Manager
class NotificationBadge {
    constructor() {
        this.badge = document.getElementById('nav-notification-badge');
        if (this.badge) {
            this.updateBadge();
            this.startPolling();
        }
    }

    async updateBadge() {
        try {
            const response = await fetch('/app/api/notifications?limit=1&unread_only=true', {
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success && this.badge) {
                const count = data.unread_count;
                if (count > 0) {
                    this.badge.textContent = count > 99 ? '99+' : count;
                    this.badge.style.display = 'inline-block';
                } else {
                    this.badge.style.display = 'none';
                }
            }
        } catch (error) {
            console.debug('Error updating notification badge:', error);
        }
    }

    startPolling() {
        // Update badge every 60 seconds
        setInterval(() => {
            this.updateBadge();
        }, 60000);
    }
}

// Initialize badge when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NotificationBadge();
});
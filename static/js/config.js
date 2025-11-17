// API Configuration
// This file provides the base URL for API calls
// It automatically detects the correct base path

const API_CONFIG = {
    // Get the base path from the current URL
    // If the app is hosted at example.com/app, this will be '/app'
    // If hosted at example.com/, this will be ''
    getBasePath() {
        const path = window.location.pathname;
        // Check if we're under /app path
        if (path.startsWith('/app/') || path === '/app') {
            return '/app';
        }
        return '';
    },
    
    // Get full API URL
    getApiUrl(endpoint) {
        const basePath = this.getBasePath();
        // Remove leading slash from endpoint if present
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
        return `${basePath}/${cleanEndpoint}`;
    }
};

// Export for use in other scripts
window.API_CONFIG = API_CONFIG;

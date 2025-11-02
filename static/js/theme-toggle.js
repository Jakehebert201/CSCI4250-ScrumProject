// Dark Mode Toggle Functionality
(function() {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Apply the saved theme immediately to prevent flash
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Create and insert the theme toggle
    function createThemeToggle() {
        const toggle = document.createElement('div');
        toggle.className = 'theme-toggle';
        toggle.innerHTML = `
            <span class="theme-toggle-icon sun-icon">☀️</span>
            <div class="theme-toggle-switch"></div>
            <span class="theme-toggle-icon moon-icon">🌙</span>
        `;
        
        // Position the toggle based on page layout
        positionToggle(toggle);
        
        toggle.addEventListener('click', toggleTheme);
        document.body.appendChild(toggle);
    }
    
    // Smart positioning based on page content
    function positionToggle(toggle) {
        const hasPageHeader = document.querySelector('.page-header');
        const hasHero = document.querySelector('.hero');
        const isLoginPage = document.querySelector('.login');
        
        if (hasPageHeader) {
            // Dashboard pages - position below header
            toggle.style.top = '100px';
        } else if (hasHero || isLoginPage) {
            // Landing page or login pages - position at top
            toggle.style.top = '20px';
        } else {
            // Default positioning
            toggle.style.top = '80px';
        }
    }
    
    // Toggle between light and dark themes
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Apply the new theme
        document.documentElement.setAttribute('data-theme', newTheme);
        
        // Save the preference
        localStorage.setItem('theme', newTheme);
        
        // Add a nice animation effect
        document.body.style.transition = 'background-color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createThemeToggle);
    } else {
        createThemeToggle();
    }
})();
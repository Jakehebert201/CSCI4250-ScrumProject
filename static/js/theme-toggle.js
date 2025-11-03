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
        
        // Force update of all text elements that might have inline styles
        updateTextColors(newTheme);
        
        // Add a nice animation effect
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }
    
    // Force update text colors for elements with inline styles
    function updateTextColors(theme) {
        const textColor = theme === 'dark' ? '#e4e6ea' : '#1c1c24';
        const mutedColor = theme === 'dark' ? 'rgba(228, 230, 234, 0.75)' : 'rgba(28, 28, 36, 0.75)';
        
        // Update elements with opacity-based colors
        const elementsWithOpacity = document.querySelectorAll('[style*="opacity"]');
        elementsWithOpacity.forEach(el => {
            if (el.style.color && el.style.color.includes('rgba(30, 30, 36')) {
                el.style.color = theme === 'dark' ? mutedColor : el.style.color;
            }
        });
        
        // Update any remaining problematic text
        const allTextElements = document.querySelectorAll('p, span, div, small, label');
        allTextElements.forEach(el => {
            const computedStyle = window.getComputedStyle(el);
            if (computedStyle.color === 'rgb(30, 30, 36)' && theme === 'dark') {
                el.style.color = textColor;
            }
        });
        
        // Update Leaflet map popups if they exist
        const leafletPopups = document.querySelectorAll('.leaflet-popup-content');
        leafletPopups.forEach(popup => {
            popup.style.color = textColor;
            const popupElements = popup.querySelectorAll('*');
            popupElements.forEach(el => {
                el.style.color = textColor;
            });
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createThemeToggle);
    } else {
        createThemeToggle();
    }
})();
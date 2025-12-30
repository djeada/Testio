// Dropdown menu functionality
const dropDownMenuButton = document.querySelector(".dropdown__button");
const dropDownMenuContent = document.querySelector(".dropdown__content");

// If the menu is open, and we click somewhere else on the screen, close the menu.
document.addEventListener("click", () => {
    if (dropDownMenuContent && dropDownMenuContent.classList.contains("dropdown__content--show")) {
        dropDownMenuContent.classList.remove("dropdown__content--show");
    }
})

//Show the dropdown menu content when the dropdown menu button is clicked.
if (dropDownMenuButton) {
    dropDownMenuButton.addEventListener('click', (event) => {
        event.stopPropagation(); //Don't pass this click to the document.
        dropDownMenuContent.classList.toggle("dropdown__content--show");
    });

    // Keyboard accessibility for dropdown
    dropDownMenuButton.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            dropDownMenuContent.classList.toggle("dropdown__content--show");
        }
    });
}

// Theme toggle functionality
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');

// Get saved theme or prefer system preference
function getPreferredTheme() {
    const savedTheme = localStorage.getItem('testio-theme');
    if (savedTheme) {
        return savedTheme;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

// Apply theme to document
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
    localStorage.setItem('testio-theme', theme);
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    applyTheme(getPreferredTheme());
});

// Toggle theme on button click
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });
}

// Keyboard shortcut for theme toggle (Ctrl+Shift+T)
document.addEventListener('keydown', (event) => {
    if (event.ctrlKey && event.shiftKey && event.key === 'T') {
        event.preventDefault();
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    }
});

// Highlight active navigation link
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        } else if (currentPath !== '/' && href !== '/' && currentPath.startsWith(href)) {
            link.classList.add('active');
        }
    });
});
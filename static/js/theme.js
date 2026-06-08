/**
 * Dark theme toggle using Bootstrap 5.3 data-bs-theme attribute.
 * Persists choice in localStorage, respects prefers-color-scheme.
 */
(function () {
    'use strict';

    const html = document.documentElement;
    const toggleBtn = document.getElementById('theme-toggle');
    const STORAGE_KEY = 'psychologist-theme';

    function getPreferredTheme() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored === 'dark' || stored === 'light') {
            return stored;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function setTheme(theme) {
        html.setAttribute('data-bs-theme', theme);
        if (toggleBtn) {
            toggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
            toggleBtn.setAttribute('aria-label',
                theme === 'dark' ? 'Переключить на светлую тему' : 'Переключить на тёмную тему');
        }
    }

    function toggleTheme() {
        const current = html.getAttribute('data-bs-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, next);
        setTheme(next);
    }

    // Apply saved theme immediately
    setTheme(getPreferredTheme());

    // Listen for OS theme changes if no stored preference
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', function () {
        if (!localStorage.getItem(STORAGE_KEY)) {
            setTheme(mediaQuery.matches ? 'dark' : 'light');
        }
    });

    // Toggle on click
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTheme);
    }
})();

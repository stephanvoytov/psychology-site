/**
 * Theme toggle — 3 режима: ☀️ светлая → 🌗 авто → 🌙 тёмная
 * Сохраняет в localStorage('psychologist-theme')
 * Flash prevention — inline-скрипт в <head>
 */
(function () {
    'use strict';

    const html = document.documentElement;
    const toggleBtn = document.getElementById('theme-toggle');
    const KEY = 'psychologist-theme';
    const MODES = ['light', 'auto', 'dark'];
    const ICONS = { light: '☀️', auto: '🌗', dark: '🌙' };
    const LABELS = { light: 'Светлая тема', auto: 'Авто', dark: 'Тёмная тема' };

    function getStored() {
        return localStorage.getItem(KEY) || 'auto';
    }

    function resolveTheme(mode) {
        if (mode === 'dark') return 'dark';
        if (mode === 'light') return 'light';
        // auto — системные настройки
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function setTheme(mode) {
        const bs = resolveTheme(mode);
        html.setAttribute('data-bs-theme', bs);
        if (toggleBtn) {
            toggleBtn.textContent = ICONS[mode] || '🌗';
            toggleBtn.title = LABELS[mode] || 'Auto';
            toggleBtn.setAttribute('aria-label', LABELS[mode] || 'Auto');
        }
        localStorage.setItem(KEY, mode);
    }

    // Инициализация
    setTheme(getStored());

    // Слушаем изменение системной темы (для auto)
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener('change', function () {
        const stored = localStorage.getItem(KEY);
        if (!stored || stored === 'auto') {
            setTheme('auto');
        }
    });

    // Клик — циклический перебор
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            const current = getStored();
            const idx = MODES.indexOf(current);
            const next = MODES[(idx + 1) % MODES.length];
            setTheme(next);
        });
    }
})();

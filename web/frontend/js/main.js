import { api } from './api.js';
import { renderDashboard } from './components/dashboard.js';
import { renderLibrary } from './components/library.js';
import { renderSettings } from './components/settings.js';
import { renderAuth } from './components/auth.js';
import { renderProgress } from './components/progress.js';

class App {
    constructor() {
        this.user = null;
        this.currentView = 'dashboard';
        this.applyTheme();
        this.init();
    }

    applyTheme() {
        const c = localStorage.getItem('brandColor');
        if (c) document.documentElement.style.setProperty('--acc-color', c);
    }

    async init() {
        try {
            this.user = await api.getMe();
            this.setUserAvatar();
            this.navigate('dashboard');
        } catch {
            this.navigate('auth');
        }

        document.getElementById('logout-btn').addEventListener('click', () => this.logout());

        const gs = document.getElementById('global-search');
        if (gs) {
            gs.addEventListener('focus', () => {
                if (this.currentView !== 'library') this.navigate('library');
            });
        }
    }

    setUserAvatar() {
        const el = document.getElementById('user-avatar');
        if (el && this.user) {
            const name = this.user.full_name || this.user.email || '?';
            el.innerText = name.charAt(0).toUpperCase();
            el.title = name;
        }
    }

    navigate(view, ...args) {
        this.currentView = view;
        const mainView = document.getElementById('main-view');
        const topNav = document.querySelector('.top-nav');

        // Nav highlighting
        ['dashboard', 'library', 'settings'].forEach(v => {
            const el = document.getElementById(`nav-${v}`);
            if (el) el.classList.toggle('active', v === view);
        });

        if (view === 'auth') {
            if (topNav) topNav.style.display = 'none';
            renderAuth(mainView, (user) => {
                this.user = user;
                if (topNav) topNav.style.display = 'flex';
                this.setUserAvatar();
                this.navigate('dashboard');
            });
            return;
        }

        if (topNav) topNav.style.display = 'flex';

        switch (view) {
            case 'dashboard': renderDashboard(mainView, this.user); break;
            case 'library':   renderLibrary(mainView); break;
            case 'settings':  renderSettings(mainView); break;
            case 'progress':  renderProgress(mainView, args[0]); break;
        }
    }

    async logout() {
        await api.logout();
        this.user = null;
        this.navigate('auth');
    }
}

window.app = new App();

const API_BASE = '/api';

export const api = {
    async request(path, options = {}) {
        const response = await fetch(`${API_BASE}${path}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (response.status === 401) {
            // Potentially trigger logout logic if not on auth page
            if (!window.location.hash.includes('auth')) {
                // Not ideal, but simple for MVP
            }
        }

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'API request failed');
        }
        
        return response.json();
    },

    // Auth
    async login(email, password) {
        const params = new URLSearchParams();
        params.append('username', email);
        params.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params
        });
        
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Login failed' }));
            throw new Error(err.detail || 'Login failed');
        }
        return this.getMe();
    },

    async signup(email, password, fullName) {
        return this.request('/auth/signup', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name: fullName })
        });
    },

    async getMe() {
        return this.request('/auth/me');
    },

    async logout() {
        return this.request('/auth/logout', { method: 'POST' });
    },

    // Books
    async getBooks() {
        return this.request('/books/');
    },

    async getStats() {
        return this.request('/books/stats');
    },

    async createBook(data) {
        return this.request('/books/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async deleteBook(id) {
        return this.request(`/books/${id}`, { method: 'DELETE' });
    },

    // Settings
    async getKeys() {
        return this.request('/settings/');
    },

    async saveKey(service, key) {
        return this.request('/settings/', {
            method: 'POST',
            body: JSON.stringify({ service, key })
        });
    },

    async testKey(service, key) {
        return this.request('/settings/test', {
            method: 'POST',
            body: JSON.stringify({ service, key })
        });
    },

    async deleteKey(service) {
        return this.request(`/settings/${service}`, { method: 'DELETE' });
    }
};

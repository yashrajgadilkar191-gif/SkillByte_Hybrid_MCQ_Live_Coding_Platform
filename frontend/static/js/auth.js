/**
 * SKILLBYTE — Client Authentication & Session Manager (Phase 2)
 */

const Auth = {
    ACCESS_KEY: 'skillbyte_access_token',
    REFRESH_KEY: 'skillbyte_refresh_token',
    USER_KEY: 'skillbyte_user',
    IS_GUEST_KEY: 'skillbyte_is_guest',

    getAccessToken() {
        return localStorage.getItem(this.ACCESS_KEY);
    },

    getRefreshToken() {
        return localStorage.getItem(this.REFRESH_KEY);
    },

    getUser() {
        try {
            const raw = localStorage.getItem(this.USER_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    },

    isGuest() {
        return localStorage.getItem(this.IS_GUEST_KEY) === 'true';
    },

    isLoggedIn() {
        return !!this.getAccessToken();
    },

    setSession(tokens, user) {
        localStorage.removeItem(this.IS_GUEST_KEY);
        if (tokens.access) localStorage.setItem(this.ACCESS_KEY, tokens.access);
        if (tokens.refresh) localStorage.setItem(this.REFRESH_KEY, tokens.refresh);
        if (user) localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        this.updateNavUI();
    },

    setGuestMode() {
        this.clearSession();
        localStorage.setItem(this.IS_GUEST_KEY, 'true');
        const guestUser = {
            id: null,
            name: 'Guest Explorer',
            email: 'guest@skillbyte.local',
            role: 'GUEST'
        };
        localStorage.setItem(this.USER_KEY, JSON.stringify(guestUser));
        this.updateNavUI();
    },

    clearSession() {
        localStorage.removeItem(this.ACCESS_KEY);
        localStorage.removeItem(this.REFRESH_KEY);
        localStorage.removeItem(this.USER_KEY);
        localStorage.removeItem(this.IS_GUEST_KEY);
        this.updateNavUI();
    },

    async logout() {
        const refresh = this.getRefreshToken();
        const access = this.getAccessToken();

        if (refresh && access) {
            try {
                await fetch('/api/auth/logout/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${access}`
                    },
                    body: JSON.stringify({ refresh })
                });
            } catch (err) {
                console.warn('Logout notification to backend failed, clearing local state:', err);
            }
        }

        this.clearSession();
        window.location.href = '/login/';
    },

    async fetchWithAuth(url, options = {}) {
        let access = this.getAccessToken();
        options.headers = options.headers || {};

        if (access) {
            options.headers['Authorization'] = `Bearer ${access}`;
        }

        let response = await fetch(url, options);

        // Attempt refresh if access token expired (401)
        if (response.status === 401 && this.getRefreshToken()) {
            const refreshed = await this.refreshToken();
            if (refreshed) {
                options.headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
                response = await fetch(url, options);
            } else {
                this.clearSession();
                window.location.href = '/login/?expired=1';
            }
        }

        return response;
    },

    async refreshToken() {
        const refresh = this.getRefreshToken();
        if (!refresh) return false;

        try {
            const res = await fetch('/api/auth/token/refresh/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh })
            });

            if (res.ok) {
                const data = await res.json();
                localStorage.setItem(this.ACCESS_KEY, data.access);
                if (data.refresh) localStorage.setItem(this.REFRESH_KEY, data.refresh);
                return true;
            }
            return false;
        } catch (e) {
            return false;
        }
    },

    updateNavUI() {
        const authNav = document.getElementById('navbar-auth-links');
        if (!authNav) return;

        if (this.isLoggedIn()) {
            const user = this.getUser();
            const roleBadgeClass = user?.role === 'ADMIN' ? 'bg-danger' : 'bg-primary';
            const adminLink = user?.role === 'ADMIN' ? `<a href="/admin/questions/" class="btn btn-outline-warning btn-sm"><i class="bi bi-shield-lock-fill me-1"></i>Question Bank</a>` : '';
            const adminLinks = user?.role === 'ADMIN' ? `
                <a href="/admin/questions/" class="btn btn-outline-warning btn-sm"><i class="bi bi-shield-lock-fill me-1"></i>Question Bank</a>
                <a href="/admin/analytics/" class="btn btn-outline-info btn-sm"><i class="bi bi-graph-up me-1"></i>Analytics</a>
            ` : '';
            authNav.innerHTML = `
                <div class="d-flex align-items-center gap-2">
                    <span class="text-light small">Hello, <strong>${escapeHtml(user?.name || 'User')}</strong></span>
                    <span class="badge ${roleBadgeClass} small">${escapeHtml(user?.role || 'STUDENT')}</span>
                    ${adminLink}
                    ${adminLinks}
                    <a href="/dashboard/" class="btn btn-outline-info btn-sm">Dashboard</a>
                    <a href="/leaderboard/" class="btn btn-outline-warning btn-sm"><i class="bi bi-trophy-fill me-1"></i>Leaderboard</a>
                    <a href="/attempts/" class="btn btn-outline-light btn-sm">My Attempts</a>
                    <button class="btn btn-outline-danger btn-sm" onclick="Auth.logout()">Logout</button>
                </div>
            `;
        } else if (this.isGuest()) {
            authNav.innerHTML = `
                <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-warning text-dark small">Guest Mode</span>
                    <a href="/dashboard/" class="btn btn-outline-info btn-sm">Dashboard</a>
                    <a href="/leaderboard/" class="btn btn-outline-warning btn-sm"><i class="bi bi-trophy-fill me-1"></i>Leaderboard</a>
                    <a href="/attempts/" class="btn btn-outline-light btn-sm">My Attempts</a>
                    <a href="/login/" class="btn btn-primary btn-sm">Login</a>
                    <a href="/register/" class="btn btn-outline-light btn-sm">Register</a>
                </div>
            `;
        } else {
            authNav.innerHTML = `
                <div class="d-flex align-items-center gap-2">
                    <a href="/leaderboard/" class="btn btn-outline-warning btn-sm"><i class="bi bi-trophy-fill me-1"></i>Leaderboard</a>
                    <button class="btn btn-outline-warning btn-sm" onclick="Auth.setGuestMode(); window.location.href='/dashboard/';">Continue as Guest</button>
                    <a href="/login/" class="btn btn-outline-light btn-sm">Login</a>
                    <a href="/register/" class="btn btn-primary btn-sm">Register</a>
                </div>
            `;
        }
    }
};

window.Auth = Auth;

function escapeHtml(string) {
    const div = document.createElement('div');
    div.innerText = string;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    Auth.updateNavUI();
});


/**
 * SKILLBYTE — Main JavaScript Foundation
 * Theme Management (Dark, Light, Mixed) & System Diagnostics
 */

const ThemeManager = {
    KEY: 'skillbyte_theme',
    DEFAULT: 'light',

    init() {
        const theme = this.getTheme();
        this.applyTheme(theme);
    },

    getTheme() {
        return localStorage.getItem(this.KEY) || this.DEFAULT;
    },

    setTheme(theme) {
        if (!['dark', 'light', 'mixed'].includes(theme)) {
            theme = this.DEFAULT;
        }
        localStorage.setItem(this.KEY, theme);
        this.applyTheme(theme);
    },

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        const icon = document.getElementById('current-theme-icon');
        const label = document.getElementById('current-theme-label');

        if (icon && label) {
            if (theme === 'dark') {
                icon.className = 'bi bi-moon-stars-fill text-info';
                label.textContent = 'Dark';
            } else if (theme === 'light') {
                icon.className = 'bi bi-sun-fill text-warning';
                label.textContent = 'Light';
            } else if (theme === 'mixed') {
                icon.className = 'bi bi-circle-half text-primary';
                label.textContent = 'Mixed';
            }
        }

        // Update active checkmarks and menu item states
        ['dark', 'light', 'mixed'].forEach(t => {
            const check = document.querySelector(`.theme-check-${t}`);
            const item = document.querySelector(`.theme-item-${t}`);
            if (check) {
                if (t === theme) {
                    check.classList.remove('d-none');
                } else {
                    check.classList.add('d-none');
                }
            }
            if (item) {
                if (t === theme) {
                    item.classList.add('active', 'fw-bold');
                } else {
                    item.classList.remove('active', 'fw-bold');
                }
            }
        });
    }
};

window.ThemeManager = ThemeManager;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    BinaryLoader1001.init();
    checkBackendHealth();
});

/**
 * SkillByte Digital 1001 Binary Loading Enhancement
 * Displays compact animated 1001 binary tag with micro pulse, keeping sizes very small on laptop viewports.
 */
const BinaryLoader1001 = {
    PATTERNS: ['1001', '1010', '1001', '0101', '1001', '1100'],

    init() {
        this.enhanceSpinners();

        // Observe DOM for dynamic spinner insertions (e.g. during AJAX submissions)
        try {
            const observer = new MutationObserver(() => {
                this.enhanceSpinners();
            });
            observer.observe(document.body, { childList: true, subtree: true });
        } catch (e) {
            // Fallback for older browsers
        }

        // Periodic high-tech micro cycle
        setInterval(() => {
            this.cyclePulse();
        }, 650);
    },

    enhanceSpinners() {
        const spinners = document.querySelectorAll('.spinner-border:not([data-sb-enhanced]), .spinner-grow:not([data-sb-enhanced])');
        spinners.forEach(spinner => {
            spinner.setAttribute('data-sb-enhanced', 'true');

            // Do not duplicate if container or sibling already has a 1001 tag
            const parent = spinner.parentElement;
            if (!parent || parent.querySelector('.sb-1001-tag')) return;

            const tag = document.createElement('span');
            tag.className = 'sb-1001-tag font-monospace';
            tag.textContent = '1001';
            tag.title = 'SkillByte Binary 1001';

            if (spinner.closest('button, .btn')) {
                tag.classList.add('sb-1001-btn');
            }

            // Insert immediately after spinner
            spinner.insertAdjacentElement('afterend', tag);
        });
    },

    cyclePulse() {
        const tags = document.querySelectorAll('.sb-1001-tag');
        if (!tags.length) return;
        const randomPattern = this.PATTERNS[Math.floor(Math.random() * this.PATTERNS.length)];
        tags.forEach(t => {
            // Micro toggle with dominant 1001
            t.textContent = (Math.random() > 0.35) ? '1001' : randomPattern;
        });
    }
};

window.BinaryLoader1001 = BinaryLoader1001;

async function checkBackendHealth() {
    const badge = document.getElementById('api-status-badge');
    const badgeText = document.getElementById('api-status-text');
    const liveResponse = document.getElementById('health-live-response');

    try {
        const response = await fetch('/api/health/');
        if (!response.ok) {
            throw new Error(`HTTP Error ${response.status}`);
        }
        const data = await response.json();

        // Update Navbar Status Badge if present
        if (badge && badgeText) {
            badge.className = 'badge rounded-pill badge-connected d-flex align-items-center gap-1';
            badgeText.textContent = `${data.service} Online`;
        }

        // Update Live Response block if present
        if (liveResponse) {
            liveResponse.innerHTML = `<span class="text-success">${JSON.stringify(data, null, 2)}</span>`;
        }
    } catch (err) {
        if (badge && badgeText) {
            badge.className = 'badge rounded-pill badge-error d-flex align-items-center gap-1';
            badgeText.textContent = 'API Offline';
        }
        if (liveResponse) {
            liveResponse.innerHTML = `<span class="text-danger">Failed to connect to /api/health/: ${err.message}</span>`;
        }
    }
}

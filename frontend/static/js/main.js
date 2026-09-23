/**
 * SKILLBYTE — Main JavaScript Foundation (Phase 1)
 */

document.addEventListener('DOMContentLoaded', () => {
    checkBackendHealth();
});

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

        // Update Navbar Status Badge
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


// Shared helpers for teacher pages.
//
// Teacher endpoints are authenticated with an HttpOnly session cookie set by
// /api/auth/login (see /login). teacherFetch sends it and, when the session
// is missing or expired (HTTP 401), sends the browser to the login page.

function redirectToLogin() {
    const next = window.location.pathname + window.location.search;
    window.location.assign('/login?next=' + encodeURIComponent(next));
}

async function teacherFetch(url, options) {
    const response = await fetch(url, Object.assign({ credentials: 'same-origin' }, options || {}));
    if (response.status === 401) {
        redirectToLogin();
        throw new Error('Your teacher session has expired. Please log in again.');
    }
    return response;
}

// Extract a human-readable message from an error response body.
async function responseErrorMessage(response, fallback) {
    try {
        const data = await response.json();
        if (typeof data.detail === 'string') return data.detail;
        if (Array.isArray(data.detail) && data.detail.length && data.detail[0].msg) {
            return data.detail.map(item => item.msg).join('; ');
        }
        if (typeof data.message === 'string') return data.message;
    } catch (e) {
        // Not JSON.
    }
    return fallback;
}

// Wire the menubar "Logout" entry.
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-action="logout"]').forEach(function (item) {
        item.addEventListener('click', async function () {
            await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
            window.location.assign('/login');
        });
    });
});

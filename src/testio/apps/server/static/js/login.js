// Teacher login: exchanges the API key for an HttpOnly session cookie.
(function () {
    const form = document.getElementById('login-form');
    if (!form) return;

    const input = document.getElementById('api-key-input');
    const button = document.getElementById('login-btn');
    const errorBox = document.getElementById('login-error');

    function nextUrl() {
        const next = new URLSearchParams(window.location.search).get('next') || '/';
        // Only same-origin paths: no "//host" or "scheme:" redirects.
        return next.startsWith('/') && !next.startsWith('//') ? next : '/';
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.hidden = false;
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        errorBox.hidden = true;
        button.disabled = true;
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ api_key: input.value })
            });
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Login failed');
            }
            window.location.assign(nextUrl());
        } catch (error) {
            showError(error.message || 'Login failed');
        } finally {
            button.disabled = false;
        }
    });
})();

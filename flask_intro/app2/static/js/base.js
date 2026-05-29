// This handles the mobile hamburger menu toggle
function toggleMenu() {
    document.getElementById("navbar").classList.toggle("active");
}

document.addEventListener("DOMContentLoaded", function () {

    // This handles the account dropdown hover on desktop
    const dropdown = document.querySelector(".dropdown");
    if (dropdown) {
        dropdown.addEventListener("mouseenter", function () {
            const menu = this.querySelector(".dropdown-menu");
            if (menu) menu.style.display = "block";
        });
        dropdown.addEventListener("mouseleave", function () {
            const menu = this.querySelector(".dropdown-menu");
            if (menu) menu.style.display = "none";
        });
    }

    // This auto-injects the CSRF token into every form and every fetch() call on the page
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        const token = csrfMeta.getAttribute('content');

        document.querySelectorAll('form').forEach(function (form) {
            const input = document.createElement('input');
            input.type  = 'hidden';
            input.name  = 'csrf_token';
            input.value = token;
            form.appendChild(input);
        });

        const originalFetch = window.fetch;
        window.fetch = function (url, options) {
            options         = options || {};
            options.headers = options.headers || {};
            options.headers['X-CSRFToken'] = token;
            return originalFetch(url, options);
        };
    }

});
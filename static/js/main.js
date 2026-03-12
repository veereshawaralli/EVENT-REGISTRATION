/**
 * EventHub — Main JavaScript
 * Lightweight enhancements (no framework required).
 */

document.addEventListener("DOMContentLoaded", () => {
    // ---------------------------------------------------------------
    // Auto-dismiss Bootstrap alerts after 5 seconds
    // ---------------------------------------------------------------
    document.querySelectorAll(".alert-dismissible").forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // ---------------------------------------------------------------
    // Smooth-scroll for same-page anchor links
    // ---------------------------------------------------------------
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (e) => {
            const target = document.querySelector(anchor.getAttribute("href"));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: "smooth" });
            }
        });
    });

    // ---------------------------------------------------------------
    // Add active class to current nav link
    // ---------------------------------------------------------------
    const currentPath = window.location.pathname;
    document.querySelectorAll(".navbar-nav .nav-link").forEach((link) => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }
    });
});

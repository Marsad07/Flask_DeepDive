    // This is for the +/- quantity buttons
    function changeQty(btn, delta) {
        const input = btn.parentElement.querySelector('.order-qty-input');
        const current = parseInt(input.value) || 1;
        const next = Math.min(10, Math.max(1, current + delta));
        input.value = next;
    }

    // This is for scroll animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('visible');
        });
    }, { threshold: 0.08 });

    document.querySelectorAll('.order-category, .order-item-card').forEach(el => {
        observer.observe(el);
    });
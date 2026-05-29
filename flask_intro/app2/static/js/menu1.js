    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('visible');
        });
    }, { threshold: 0.08 });

    document.querySelectorAll(
        '.menu-header, .menu-category, .menu-item'
    ).forEach(el => observer.observe(el));
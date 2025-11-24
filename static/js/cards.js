document.addEventListener('DOMContentLoaded', () => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    const initCountUps = (reduceMotion) => {
        const counters = document.querySelectorAll('.countup[data-target]');
        counters.forEach((el) => {
            const target = parseInt(el.dataset.target, 10);
            if (Number.isNaN(target)) {
                return;
            }

            if (reduceMotion) {
                el.textContent = target.toLocaleString();
                return;
            }

            let start = null;
            const duration = 960;
            const updateCounter = (timestamp) => {
                if (!start) {
                    start = timestamp;
                }
                const progress = Math.min((timestamp - start) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(eased * target);

                el.textContent = current.toLocaleString();

                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                }
            };

            requestAnimationFrame(updateCounter);
        });
    };

    const initFeatureObserver = (reduceMotion) => {
        const featureCards = document.querySelectorAll('.card-feature');

        if (featureCards.length === 0) {
            return;
        }

        if (reduceMotion || typeof IntersectionObserver === 'undefined') {
            featureCards.forEach((card) => {
                card.style.opacity = 1;
                card.style.transform = 'translateY(0)';
            });
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = 1;
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });

        featureCards.forEach((card) => {
            card.style.opacity = 0;
            card.style.transform = 'translateY(30px)';
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(card);
        });
    };

    const initReservedPulse = (reduceMotion) => {
        if (reduceMotion) {
            document
                .querySelectorAll('.card-reserved')
                .forEach((card) => card.classList.remove('active'));
        }
    };

    const handleMotionPreference = (event) => {
        const reduceMotion = event.matches;
        initCountUps(reduceMotion);
        initFeatureObserver(reduceMotion);
        initReservedPulse(reduceMotion);
    };

    const reduceMotion = prefersReducedMotion.matches;
    initCountUps(reduceMotion);
    initFeatureObserver(reduceMotion);
    initReservedPulse(reduceMotion);

    prefersReducedMotion.addEventListener('change', handleMotionPreference);
});


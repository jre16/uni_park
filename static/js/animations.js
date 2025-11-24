(() => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const select = (selector, scope = document) => scope.querySelector(selector);
  const selectAll = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

  function animateCountUp() {
    const counters = selectAll('[data-count-up]');
    if (!counters.length) return;

    const duration = 2200;

    const animate = (el, value) => {
      const start = performance.now();
      const formatter = new Intl.NumberFormat();

      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = prefersReducedMotion.matches ? progress : 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(value * eased);
        el.textContent = formatter.format(current);
        if (progress < 1) requestAnimationFrame(tick);
      };

      requestAnimationFrame(tick);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !entry.target.dataset.counted) {
            entry.target.dataset.counted = 'true';
            const targetValue = parseFloat(entry.target.dataset.countUp || '0');
            if (!Number.isNaN(targetValue)) animate(entry.target, targetValue);
          }
        });
      },
      { threshold: 0.5 }
    );

    counters.forEach((counter) => {
      counter.textContent = counter.dataset.prefill || '0';
      observer.observe(counter);
    });
  }

  function initParallax() {
    const nodes = selectAll('[data-parallax]');
    if (!nodes.length || prefersReducedMotion.matches) return;

    const handle = () => {
      const scrollY = window.scrollY;
      nodes.forEach((node) => {
        const depth = parseFloat(node.dataset.parallaxDepth || '20');
        const translate = (scrollY / depth) * -1;
        node.style.transform = `translate3d(0, ${translate}px, 0)`;
      });
    };

    handle();
    window.addEventListener('scroll', handle, { passive: true });
  }

  function initHeroTimeline() {
    const hero = select('[data-hero]');
    if (!hero) return;

    if (typeof gsap !== 'undefined' && !prefersReducedMotion.matches) {
      const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
      tl.fromTo(
        '[data-hero-headline]',
        { y: 60, opacity: 0 },
        { y: 0, opacity: 1, duration: 1.15 }
      )
        .fromTo(
          '[data-hero-subhead]',
          { y: 40, opacity: 0 },
          { y: 0, opacity: 0.9, duration: 1 },
          '-=0.7'
        )
        .fromTo(
          '[data-hero-cta]',
          { y: 30, opacity: 0, scale: 0.94 },
          { y: 0, opacity: 1, scale: 1, duration: 0.6 },
          '-=0.5'
        )
        .fromTo(
          '[data-hero-stats] .hero__stat',
          { y: 35, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.7,
            stagger: 0.12,
            ease: 'power3.out',
          },
          '-=0.35'
        );
    } else {
      selectAll('[data-hero-headline], [data-hero-subhead], [data-hero-cta]').forEach((node) => {
        node.style.opacity = '1';
        node.style.transform = 'translateY(0)';
      });
    }
  }

  function initCardEntrance(scope = document) {
    const card = select('[data-hero-card]', scope);
    if (!card) return;
    if (prefersReducedMotion.matches) {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
      return;
    }

    card.style.opacity = '0';
    card.style.transform = 'translateY(40px) scale(0.96)';

    requestAnimationFrame(() => {
      if (typeof gsap !== 'undefined') {
        gsap.fromTo(
          card,
          { y: 45, scale: 0.95, opacity: 0 },
          { y: 0, scale: 1, opacity: 1, duration: 0.85, ease: 'expo.out' }
        );
      } else {
        card.style.transition =
          'transform 0.7s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.6s ease';
        card.style.transform = 'translateY(0) scale(1)';
        card.style.opacity = '1';
      }
    });
  }

  function initFloatingPins(scope = document) {
    const pins = selectAll('[data-pin]', scope);
    if (!pins.length || typeof gsap === 'undefined' || prefersReducedMotion.matches) return;
    pins.forEach((pin, index) => {
      gsap.fromTo(
        pin,
        { y: gsap.utils.random(-12, 12), opacity: 0 },
        {
          y: gsap.utils.random(-6, 6),
          opacity: 1,
          duration: gsap.utils.random(1.8, 2.4),
          delay: 0.4 + index * 0.18,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
        }
      );
    });
  }

  function initMagneticButton() {
    const button = select('[data-hero-cta]');
    if (!button || typeof gsap === 'undefined' || prefersReducedMotion.matches) return;

    const strength = 16;
    const reset = () => gsap.to(button, { x: 0, y: 0, duration: 0.45, ease: 'expo.out' });

    button.addEventListener('mousemove', (event) => {
      const rect = button.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width - 0.5) * strength;
      const y = ((event.clientY - rect.top) / rect.height - 0.5) * strength;
      gsap.to(button, { x, y, duration: 0.35, ease: 'power2.out' });
    });

    button.addEventListener('mouseleave', reset);
    button.addEventListener('blur', reset, true);
  }

  function initRipple() {
    selectAll('[data-ripple]').forEach((node) => {
      node.addEventListener('pointerdown', (event) => {
        const rect = node.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 100;
        const y = ((event.clientY - rect.top) / rect.height) * 100;
        node.style.setProperty('--ripple-x', `${x}%`);
        node.style.setProperty('--ripple-y', `${y}%`);
        node.classList.add('is-pressed');
      });

      node.addEventListener('pointerup', () => {
        node.classList.remove('is-pressed');
      });
      node.addEventListener('pointerleave', () => {
        node.classList.remove('is-pressed');
      });
    });
  }

  function registerHtmx() {
    if (typeof htmx === 'undefined') return;
    document.body.addEventListener('htmx:afterSwap', (event) => {
      const target = event.target;
      if (target && target.id === 'hero-card-shell') {
        initCardEntrance(target);
        initFloatingPins(target);
      }
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    const hero = select('[data-hero]');
    if (!hero) return;

    initHeroTimeline();
    animateCountUp();
    initParallax();
    initCardEntrance();
    initFloatingPins();
    initMagneticButton();
    initRipple();
    registerHtmx();
  });
})();


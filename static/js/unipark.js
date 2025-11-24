/* global Alpine, AOS, gsap, htmx, L, bodymovin */
(() => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const leafletState = { map: null, markers: {} };

  function initTheme() {
    const root = document.documentElement;
    const stored = localStorage.getItem('unipark:theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const active = stored || (systemPrefersDark ? 'dark' : 'light');
    root.classList.toggle('dark', active === 'dark');
    localStorage.setItem('unipark:theme', active);

    document.addEventListener('toggle-theme', () => {
      const current = root.classList.contains('dark') ? 'dark' : 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      root.classList.toggle('dark', next === 'dark');
      localStorage.setItem('unipark:theme', next);
      document.cookie = `unipark_theme=${next};path=/;SameSite=Lax`;
    });
  }

  function initAOS() {
    if (typeof AOS === 'undefined') return;
    AOS.init({
      once: false,
      duration: 850,
      offset: 80,
      easing: 'ease-out-cubic',
      disable: () => prefersReducedMotion.matches,
    });
  }

  function initTestimonials() {
    if (typeof Alpine === 'undefined') return;
    document.addEventListener('alpine:init', () => {
      Alpine.data('testimonialCarousel', () => ({
        index: 0,
        interval: null,
        slides: [],
        init() {
          this.slides = Array.from(this.$el.querySelectorAll('[data-testimonial]'));
          this.start();
          this.$watch('index', (value) => {
            this.slides.forEach((slide, idx) => {
              slide.classList.toggle('opacity-100', idx === value);
              slide.classList.toggle('opacity-30', idx !== value);
            });
          });
        },
        start() {
          this.interval = setInterval(() => {
            this.index = (this.index + 1) % this.slides.length;
          }, 5000);
        },
        stop() {
          clearInterval(this.interval);
        },
        goTo(i) {
          this.index = i;
        },
      }));
    });
  }

  function toastFromHtmx() {
    if (typeof htmx === 'undefined') return;
    document.body.addEventListener('htmx:afterSwap', (event) => {
      const trigger = event.detail.xhr.getResponseHeader('X-UniPark-Toast');
      if (!trigger) return;
      try {
        const data = JSON.parse(trigger);
        document.dispatchEvent(new CustomEvent('unipark:toast', { detail: data }));
      } catch (error) {
        console.error('Failed to parse toast payload', error);
      }
    });
  }

  function initAlpineStores() {
    if (typeof Alpine === 'undefined') return;
    document.addEventListener('alpine:init', () => {
      Alpine.data('toastStack', () => ({
        toasts: [],
        init() {
          document.addEventListener('unipark:toast', (event) => {
            this.push(event.detail);
          });
        },
        push({ title = 'Success', message = '', variant = 'success' }) {
          const id = Date.now();
          const toast = { id, title, message, variant, visible: true, progress: 100 };
          this.toasts.push(toast);
          const decay = setInterval(() => {
            toast.progress -= 2;
            if (toast.progress <= 0) {
              clearInterval(decay);
              this.dismiss(id);
            }
          }, 90);
          setTimeout(() => this.dismiss(id), 4200);
        },
        dismiss(id) {
          const toast = this.toasts.find((item) => item.id === id);
          if (toast) toast.visible = false;
          this.toasts = this.toasts.filter((item) => item.visible);
        },
      }));
    });
  }

  function createMarker(map, lot) {
    const marker = L.circleMarker([lot.latitude, lot.longitude], {
      radius: 9,
      color: '#22C55E',
      fillColor: '#22C55E',
      fillOpacity: 0.85,
      weight: 2,
    })
      .addTo(map)
      .bindPopup(`<strong>${lot.title}</strong><br>${lot.address}`);
    return marker;
  }

  function updateLeafletLots(lots) {
    if (!leafletState.map) return;
    Object.values(leafletState.markers).forEach((marker) => leafletState.map.removeLayer(marker));
    leafletState.markers = {};
    lots.forEach((lot) => {
      const marker = createMarker(leafletState.map, lot);
      leafletState.markers[lot.id] = marker;
    });
    if (lots.length) {
      const first = lots[0];
      leafletState.map.panTo([first.latitude, first.longitude]);
    }
  }

  function initLeaflet() {
    if (typeof L === 'undefined') return;
    const wrapper = document.getElementById('parking-map');
    if (!wrapper) return;

    const { lots } = wrapper.dataset;
    const parsed = lots ? JSON.parse(lots) : [];

    const map = L.map('parking-map', {
      scrollWheelZoom: false,
      zoomControl: false,
      attributionControl: false,
    }).setView([33.8938, 35.5018], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
    }).addTo(map);

    leafletState.markers = {};
    parsed.forEach((lot) => {
      const marker = createMarker(map, lot);
      leafletState.markers[lot.id] = marker;
    });

    leafletState.map = map;

    document.addEventListener('lot-focus', (event) => {
      const { id } = event.detail;
      const marker = leafletState.markers[id];
      if (!marker) return;
      map.panTo(marker.getLatLng());
      marker.setStyle({ color: '#7C2AE8', fillColor: '#7C2AE8' });
    });

    document.addEventListener('lot-blur', (event) => {
      const { id } = event.detail;
      const marker = leafletState.markers[id];
      if (!marker) return;
      marker.setStyle({ color: '#22C55E', fillColor: '#22C55E' });
    });
  }

  function initLottieEmptyState() {
    if (typeof bodymovin === 'undefined') return;
    const target = document.getElementById('empty-lottie');
    if (!target) return;
    bodymovin.loadAnimation({
      container: target,
      renderer: 'svg',
      loop: true,
      autoplay: true,
      path: target.dataset.src,
    });
  }

  function initDashboard() {
    if (prefersReducedMotion.matches) return;
    const cards = document.querySelectorAll('[data-dashboard-card]');
    if (!cards.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.transform = 'translateY(0)';
            entry.target.style.opacity = '1';
          }
        });
      },
      { threshold: 0.4 }
    );

    cards.forEach((card, index) => {
      card.style.transform = 'translateY(30px)';
      card.style.opacity = '0';
      card.style.transition = `transform 0.65s cubic-bezier(0.22, 1, 0.36, 1) ${(index * 80) / 1000}s, opacity 0.6s ease ${(index * 80) / 1000}s`;
      observer.observe(card);
    });
  }

  function initAccessibilityControls() {
    const fontButtons = document.querySelectorAll('[data-font]');
    const contrastToggle = document.getElementById('high-contrast-toggle');

    fontButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const scale = button.dataset.font;
        const map = { base: 1, large: 1.1, xl: 1.2 };
        const value = map[scale] || 1;
        document.documentElement.style.setProperty('--font-scale', value);
        localStorage.setItem('unipark:font-scale', value);
      });
    });

    if (contrastToggle) {
      const stored = localStorage.getItem('unipark:contrast') === 'true';
      contrastToggle.checked = stored;
      document.documentElement.classList.toggle('high-contrast', stored);
      contrastToggle.addEventListener('change', () => {
        document.documentElement.classList.toggle('high-contrast', contrastToggle.checked);
        localStorage.setItem('unipark:contrast', contrastToggle.checked);
      });
    }

    const storedScale = parseFloat(localStorage.getItem('unipark:font-scale') || '1');
    document.documentElement.style.setProperty('--font-scale', storedScale);
  }

  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initAOS();
    initLeaflet();
    initLottieEmptyState();
    initDashboard();
    initTestimonials();
    initAlpineStores();
    toastFromHtmx();
    initAccessibilityControls();
  });

  document.body.addEventListener('map:update', (event) => {
    if (!event.detail) return;
    updateLeafletLots(event.detail.lots || []);
  });
})();


(() => {
  const ready = (fn) => {
    if (document.readyState !== "loading") {
      fn();
    } else {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    }
  };

  const debounce = (fn, wait = 250) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(null, args), wait);
    };
  };

  const scorePassword = (value) => {
    if (!value) return 0;
    let score = 0;
    if (value.length >= 8) score += 1;
    if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score += 1;
    if (/\d/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;
    return Math.min(score, 4);
  };

  const validators = {
    username(value) {
      if (!value) return "Enter the email or phone linked to your account.";
      if (value.includes("@")) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
          ? ""
          : "Looks like an invalid email. Example: name@example.com";
      }
      const digits = value.replace(/\D/g, "");
      if (digits.length < 10 || digits.length > 15) {
        return "Phone numbers should be 10–15 digits.";
      }
      return "";
    },
    email(value) {
      if (!value) return "We’ll use this for receipts and verifications.";
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
        ? ""
        : "Use a valid email format like name@example.com.";
    },
    phone(value) {
      if (!value) return "Optional, but it speeds up recovery and SMS alerts.";
      const digits = value.replace(/\D/g, "");
      if (digits.length < 10 || digits.length > 15) {
        return "Use 10–15 digits. Country codes welcome.";
      }
      return "";
    },
    password(value) {
      if (!value) return "Passwords are case-sensitive.";
      return value.length >= 8 ? "" : "Use 8+ characters for a secure passphrase.";
    },
    "password-confirm": (value) => {
      const pw1 = document.querySelector('#signup-form input[name="password1"]');
      if (!pw1) return "";
      if (!value) return "Repeat your password to confirm.";
      return pw1.value === value ? "" : "Passwords need to match.";
    },
  };

  ready(() => {
    // Floating label state management
    const updateFieldState = (input) => {
      const wrapper = input.closest("[data-field-wrapper]");
      if (!wrapper) return;
      const hasValue = input.value && input.value.trim().length > 0;
      wrapper.classList.toggle("is-filled", hasValue);
      if (!input.value) {
        input.setAttribute("aria-invalid", "false");
      }
    };

    document.querySelectorAll("[data-field-wrapper] input").forEach((input) => {
      updateFieldState(input);
      input.addEventListener("input", () => updateFieldState(input));
      input.addEventListener("blur", () => updateFieldState(input));
    });

    // Password visibility toggles
    document.querySelectorAll(".pw-toggle").forEach((btn) => {
      btn.addEventListener("click", () => {
        const controlId = btn.getAttribute("aria-controls");
        const input =
          (controlId && document.getElementById(controlId)) ||
          btn.previousElementSibling?.querySelector("input[type='password']");
        if (!input) return;
        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";
        btn.setAttribute("aria-pressed", String(isPassword));
        btn.textContent = isPassword ? "Hide" : "Show";
        if (!isPassword) {
          input.setAttribute("aria-live", "assertive");
        } else {
          input.removeAttribute("aria-live");
        }
      });
    });

    // Caps lock hint
    const passwordInput = document.querySelector("#login-form input[type='password']");
    const capsHint = document.getElementById("caps-hint");
    const updateCapsLock = (event) => {
      if (!capsHint) return;
      const capsOn = event.getModifierState && event.getModifierState("CapsLock");
      capsHint.hidden = !capsOn;
    };
    if (passwordInput) {
      passwordInput.addEventListener("keydown", updateCapsLock);
      passwordInput.addEventListener("keyup", updateCapsLock);
    }

    // Password strength meter
    const pwField = document.querySelector('#signup-form input[name="password1"]');
    const meter = document.getElementById("pw-meter");
    const hint = document.getElementById("pw-hint");
    const meterClasses = ["weak", "medium", "good", "strong"];

    const refreshMeter = () => {
      if (!pwField || !meter) return;
      const score = scorePassword(pwField.value);
      meter.classList.remove(...meterClasses);
      if (score > 0) {
        meter.classList.add(meterClasses[Math.max(0, score - 1)]);
      }
      if (hint) {
        hint.textContent =
          score < 3
            ? "Add upper/lowercase, numbers, and a symbol."
            : "Strong choice. Keep it memorable.";
      }
    };

    if (pwField) {
      refreshMeter();
      pwField.addEventListener("input", debounce(refreshMeter, 120));
    }

    // Debounced hint validation
    const applyHint = (input) => {
      const validateKey = input.dataset.validate;
      if (!validateKey) return;
      const helper = input
        .closest("[data-field-wrapper]")
        ?.querySelector("[data-help]");
      if (!helper) return;
      const validator = validators[validateKey];
      if (!validator) return;
      const message = validator(input.value);
      helper.textContent = message;
      helper.hidden = !message;
      const ariaInvalid = message ? "true" : "false";
      input.setAttribute("aria-invalid", ariaInvalid);
    };

    document.querySelectorAll("[data-field-wrapper] input").forEach((input) => {
      const debounced = debounce(() => applyHint(input), 180);
      input.addEventListener("input", debounced);
      input.addEventListener("blur", () => applyHint(input));
    });

    // Submit loading state
    ["signup-form", "login-form"].forEach((formId) => {
      const form = document.getElementById(formId);
      if (!form) return;
      const submitButton = form.querySelector("button[type='submit'], .btn-primary");
      const originalText = submitButton ? submitButton.textContent : "";
      form.addEventListener("submit", () => {
        if (!submitButton) return;
        submitButton.disabled = true;
        submitButton.setAttribute("aria-busy", "true");
        submitButton.innerHTML =
          '<span class="loader"><span></span><span></span><span></span></span>';
        setTimeout(() => {
          // Revert after 8s in case of network errors (safe guard)
          if (submitButton.disabled) {
            submitButton.disabled = false;
            submitButton.removeAttribute("aria-busy");
            submitButton.textContent = originalText;
          }
        }, 8000);
      });
    });

    // Shake on server-side validation errors
    document.querySelectorAll(".has-error").forEach((field) => {
      field.classList.add("shake");
      setTimeout(() => field.classList.remove("shake"), 900);
    });

    // Car Animation Controller
    const visual = document.querySelector('.signup-hero__visual');
    const car = document.querySelector('.parking-car');
    const letter = document.querySelector('.visual-spot__letter');

    if (visual && car && letter) {
      // Respect user's motion preferences
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (prefersReducedMotion) {
        // Skip to final state for users who prefer reduced motion
        visual.setAttribute('data-paused', 'true');
        car.style.opacity = '0';
        car.style.visibility = 'hidden';
        letter.style.opacity = '1';
        letter.style.visibility = 'visible';
        letter.style.transform = 'translateY(0) scale(1) rotate(180deg)';
        letter.style.transformOrigin = 'center bottom';
      } else {
        // Add pause/play functionality (optional - for debugging or user control)
        let isPaused = false;

        visual.addEventListener('click', () => {
          isPaused = !isPaused;
          visual.setAttribute('data-paused', isPaused);
        });

        // Ensure animations complete properly
        car.addEventListener('animationend', (e) => {
          if (e.animationName === 'car-park-morph-once') {
            // Ensure car is hidden at the end
            car.style.opacity = '0';
            car.style.visibility = 'hidden';
          }
        });

        letter.addEventListener('animationend', (e) => {
          if (e.animationName === 'letter-reveal-once') {
            // Ensure letter stays visible
            letter.style.opacity = '1';
            letter.style.visibility = 'visible';
          }
        });

        // Optional: Restart animation on page visibility change
        document.addEventListener('visibilitychange', () => {
          if (!document.hidden && !prefersReducedMotion) {
            // Reset animations when page becomes visible again
            const animations = [
              car, letter,
              ...document.querySelectorAll('.car-wheel'),
              ...document.querySelectorAll('.car-light'),
              document.querySelector('.car-shadow')
            ].filter(Boolean);

            animations.forEach(el => {
              el.style.animation = 'none';
              el.offsetHeight; // Trigger reflow
              el.style.animation = null;
            });
          }
        });

        // Log animation progress (for debugging)
        if (window.location.search.includes('debug')) {
          let lastPercent = 0;
          const checkProgress = setInterval(() => {
            const computed = window.getComputedStyle(car);
            const transform = computed.transform;

            // Simple progress tracking based on transform
            if (transform !== 'none') {
              const matrix = new DOMMatrix(transform);
              const currentX = matrix.m41;
              const progress = Math.round((currentX / window.innerWidth) * 100);

              if (progress !== lastPercent) {
                console.log(`Animation progress: ${progress}%`);
                lastPercent = progress;
              }
            }
          }, 100);

          // Clear after animation completes (2 seconds)
          setTimeout(() => clearInterval(checkProgress), 2500);
        }
      }
    }

    // Add smooth entrance animation for the entire visual element
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
        }
      });
    }, { threshold: 0.2 });

    const heroVisual = document.querySelector('.signup-hero__visual');
    if (heroVisual) {
      observer.observe(heroVisual);
    }
  });
})();


const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

const debounce = (fn, ms = 300) => {
  let timeout;
  return (...args) => {
    window.clearTimeout(timeout);
    timeout = window.setTimeout(() => fn(...args), ms);
  };
};

const filtersForm = $('#filters-form');
const searchInput = $('#search');
const liveButton = $('#btn-live');
const mapButton = $('#toggle-map');
const mapDrawer = $('#map-drawer');
const resultsPane = $('.results-pane');
const resultsGrid = $('#results-grid');
const loadMoreAnchor = $('#load-more-anchor');
const filterField = $('#selected-filter');
const sortField = $('#selected-sort');

const ensureHiddenField = (name) => {
  if (!filtersForm) return null;
  let field = filtersForm.querySelector(`input[name="${name}"]`);
  if (!field) {
    field = document.createElement('input');
    field.type = 'hidden';
    field.name = name;
    filtersForm.appendChild(field);
  }
  return field;
};

const setBusy = (state) => {
  if (resultsPane) {
    resultsPane.setAttribute('aria-busy', String(state));
    resultsPane.classList.toggle('is-loading', state);
  }
  if (resultsGrid) {
    resultsGrid.setAttribute('aria-busy', String(state));
    resultsGrid.classList.toggle('is-loading', state);
  }
};

const submitFilters = () => {
  if (!filtersForm) return;
  setBusy(true);
  if (typeof filtersForm.requestSubmit === 'function') {
    filtersForm.requestSubmit();
  } else {
    filtersForm.submit();
  }
};

const updateChipUI = (selected) => {
  $$('.chip[data-filter]').forEach((chip) => {
    const isActive = chip.dataset.filter === selected;
    chip.classList.toggle('is-active', isActive);
    chip.setAttribute('aria-pressed', String(isActive));
  });
};

const activateFilterChip = (selected) => {
  const value = selected || 'all';
  updateChipUI(value);
  const field = filterField || ensureHiddenField('filter');
  if (field) {
    field.value = value;
  }
  submitFilters();
};

updateChipUI(filterField ? filterField.value : 'all');

// SEARCH (debounced)
const handleSearch = debounce(() => {
  if (!filtersForm) return;
  submitFilters();
}, 350);

if (searchInput) {
  searchInput.addEventListener('input', handleSearch);
}

// LIVE AVAILABILITY TOGGLE
if (liveButton) {
  liveButton.addEventListener('click', () => {
    const pressed = liveButton.getAttribute('aria-pressed') === 'true';
    liveButton.setAttribute('aria-pressed', String(!pressed));
    liveButton.classList.toggle('is-active', !pressed);

    const liveField = ensureHiddenField('live');
    if (liveField) {
      if (pressed) {
        liveField.value = '';
      } else {
        liveField.value = '1';
      }
    }

    submitFilters();
  });
}

// SORT DROPDOWN

// MAP TOGGLE
if (mapButton && mapDrawer) {
  mapButton.addEventListener('click', () => {
    const open = mapButton.getAttribute('aria-pressed') === 'true';
    mapButton.setAttribute('aria-pressed', String(!open));
    if (open) {
      mapDrawer.hidden = true;
      mapDrawer.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('map-open');
    } else {
      mapDrawer.hidden = false;
      mapDrawer.setAttribute('aria-hidden', 'false');
      document.body.classList.add('map-open');
    }
  });
}

document.addEventListener('click', (event) => {
  const chip = event.target.closest('.chip[data-filter]');
  if (chip) {
    event.preventDefault();
    activateFilterChip(chip.dataset.filter);
    return;
  }

  const target = event.target;
  if (target && target.id === 'clear-filters') {
    if (filtersForm && filterField) {
      filterField.value = 'all';
    }
    updateChipUI('all');
    if (searchInput) {
      searchInput.value = '';
    }
    submitFilters();
  }
});

// INFINITE SCROLL (placeholder fetch logic)
const fetchNextPage = () => {
  if (!resultsGrid) return;
  const nextUrl = resultsGrid.dataset.nextUrl;
  if (!nextUrl) return;
  // Placeholder for future enhancement: fetch(nextUrl) and append new items.
};

if ('IntersectionObserver' in window && loadMoreAnchor) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          fetchNextPage();
        }
      });
    },
    { rootMargin: '300px 0px' }
  );
  observer.observe(loadMoreAnchor);
}

// HTMX integration hooks, if HTMX is present on the page
document.addEventListener('htmx:beforeRequest', () => setBusy(true));
document.addEventListener('htmx:afterSwap', () => setBusy(false));
document.addEventListener('htmx:responseError', () => setBusy(false));


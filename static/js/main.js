// Main JS for Marketplace
// Small helpers: accessible focus outline, sticky header offset handling, optional cart count updater

document.addEventListener('DOMContentLoaded', function () {
  // Remove focus outline only for mouse users
  (function () {
    const body = document.body;
    function handleFirstTab(e) {
      if (e.key === 'Tab') {
        body.classList.add('user-is-tabbing');
        window.removeEventListener('keydown', handleFirstTab);
      }
    }
    window.addEventListener('keydown', handleFirstTab);
  })();

  // Make navbar toggler accessible state reflected
  const toggler = document.querySelector('.navbar-toggler');
  const navbarCollapse = document.querySelector('#navbarNav');
  if (toggler && navbarCollapse) {
    toggler.addEventListener('click', function () {
      const expanded = this.getAttribute('aria-expanded') === 'true';
      this.setAttribute('aria-expanded', String(!expanded));
    });
  }

  // Optional: observe cart count element (if added server-side)
  const cartCountEl = document.querySelector('[data-cart-count]');
  if (cartCountEl) {
    // placeholder for future dynamic updates via fetch/websocket
    console.debug('Cart count element present:', cartCountEl.dataset.cartCount);
  }

  document.querySelectorAll('.order-action-btn').forEach(function (button) {
    button.addEventListener('click', function () {
      if (this.classList.contains('is-ordering')) {
        return;
      }

      this.classList.add('is-ordering');
      const label = this.querySelector('.btn-label');
      if (label) {
        label.textContent = 'Ordering...';
      }

      window.clearTimeout(this.orderTimer);
      this.orderTimer = window.setTimeout(function () {
        button.classList.remove('is-ordering');
        if (label) {
          label.textContent = 'Confirm Order';
        }
      }, 1850);
    });
  });
});

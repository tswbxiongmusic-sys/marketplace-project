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

  // Cycle through a product card's photos automatically when it has more than one.
  document.querySelectorAll('.product-image-frames').forEach(function (wrap) {
    const frames = wrap.querySelectorAll('.product-image-frame');
    if (frames.length < 2) {
      return;
    }
    let index = 0;
    window.setInterval(function () {
      frames[index].classList.remove('is-active');
      index = (index + 1) % frames.length;
      frames[index].classList.add('is-active');
    }, 2500);
  });

  // Hero carousel: slides left-to-right, with arrow + dot controls.
  const heroCarousel = document.getElementById('hero-carousel');
  if (heroCarousel) {
    const track = heroCarousel.querySelector('.hero-carousel-track');
    const slides = heroCarousel.querySelectorAll('.hero-carousel-slide');
    const dots = heroCarousel.querySelectorAll('.hero-carousel-dot');
    const prevBtn = heroCarousel.querySelector('.hero-carousel-prev');
    const nextBtn = heroCarousel.querySelector('.hero-carousel-next');
    let current = 0;
    let timer = null;

    function goTo(i) {
      current = (i + slides.length) % slides.length;
      track.style.transform = 'translateX(-' + (current * 100) + '%)';
      dots.forEach(function (dot, dotIndex) {
        dot.classList.toggle('is-active', dotIndex === current);
      });
    }

    function startAutoplay() {
      window.clearInterval(timer);
      timer = window.setInterval(function () {
        goTo(current + 1);
      }, 3500);
    }

    if (slides.length > 1) {
      if (prevBtn) {
        prevBtn.addEventListener('click', function () {
          goTo(current - 1);
          startAutoplay();
        });
      }
      if (nextBtn) {
        nextBtn.addEventListener('click', function () {
          goTo(current + 1);
          startAutoplay();
        });
      }
      dots.forEach(function (dot, dotIndex) {
        dot.addEventListener('click', function () {
          goTo(dotIndex);
          startAutoplay();
        });
      });
      startAutoplay();
    }
  }

  // Side drawer menu
  (function () {
    const toggleBtn = document.getElementById('sideMenuToggle');
    const drawer = document.getElementById('sideDrawer');
    const backdrop = document.getElementById('sideDrawerBackdrop');
    const closeBtn = document.getElementById('sideDrawerClose');
    if (!toggleBtn || !drawer || !backdrop) return;

    function openDrawer() {
      drawer.classList.add('is-open');
      backdrop.classList.add('is-open');
      drawer.setAttribute('aria-hidden', 'false');
      toggleBtn.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
      drawer.classList.remove('is-open');
      backdrop.classList.remove('is-open');
      drawer.setAttribute('aria-hidden', 'true');
      toggleBtn.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }

    toggleBtn.addEventListener('click', openDrawer);
    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    backdrop.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeDrawer();
    });
  })();
});

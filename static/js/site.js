(() => {
  const header = document.querySelector('.site-header');
  const updateHeader = () => header?.classList.toggle('is-scrolled', window.scrollY > 16);
  updateHeader();
  window.addEventListener('scroll', updateHeader, { passive: true });

  // Content stays visible without JavaScript or when reduced motion is preferred.
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    document.querySelectorAll('[data-reveal]').forEach((element) => {
      if (element.getBoundingClientRect().top >= window.innerHeight) {
        element.classList.add('reveal-ready');
        observer.observe(element);
      }
    });
  }

  const menu = document.querySelector('.site-header details');
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu?.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (menu?.open && !menu.contains(event.target)) menu.open = false;
  });
})();

(() => {
  const notice = document.querySelector('[data-legal-notice]');
  if (notice) {
    const storageKey = 'klc-legal-notice-dismissed';
    const version = notice.dataset.noticeVersion;
    let dismissed = false;
    try { dismissed = window.localStorage.getItem(storageKey) === version; }
    catch { /* The notice still works when browser storage is unavailable. */ }

    if (!dismissed) {
      notice.hidden = false;
      const reserveSpace = () => {
        const space = notice.hidden ? 0 : Math.ceil(notice.getBoundingClientRect().height) + 32;
        document.documentElement.style.setProperty('--legal-notice-space', `${space}px`);
      };
      reserveSpace();
      const observer = 'ResizeObserver' in window ? new ResizeObserver(reserveSpace) : null;
      observer?.observe(notice);
      window.addEventListener('resize', reserveSpace, { passive: true });
      notice.querySelector('[data-dismiss-legal-notice]').addEventListener('click', () => {
        notice.hidden = true;
        observer?.disconnect();
        window.removeEventListener('resize', reserveSpace);
        reserveSpace();
        try { window.localStorage.setItem(storageKey, version); }
        catch { /* Dismiss for this page even if storage is blocked. */ }
        // Restore keyboard focus to a visible element after hiding the button.
        document.querySelector('#main-content')?.focus({ preventScroll: true });
      });
    }
  }

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

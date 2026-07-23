/* page_disclosure.js — issue #23
 * Open progressive-disclosure <details> panels when a URL hash points to a
 * contained element, then focus the section heading for screen readers.
 * Works on both initial load (DOMContentLoaded) and subsequent hashchange.
 * No dependencies; degrades cleanly when JS is absent (print CSS opens all).
 */
(function () {
  'use strict';

  /**
   * Walk the DOM upward from the element at `hash` and open any enclosing
   * .page-section-disclosure <details>; then focus the nearest heading
   * inside the target so screen readers announce the section name.
   *
   * @param {string} hash  Location fragment including the leading '#'.
   */
  function revealAnchor(hash) {
    if (!hash || hash === '#') return;
    var target;
    try { target = document.querySelector(hash); } catch (_) { return; }
    if (!target) return;

    var el = target;
    while (el) {
      if (el.tagName === 'DETAILS' &&
          el.classList.contains('page-section-disclosure')) {
        if (!el.open) {
          el.open = true;
        }
        /* Focus the first heading inside the target, not the <summary> toggle,
         * so screen readers announce the section title on navigation. */
        var heading = target.querySelector('h2, h3') || target;
        if (!heading.hasAttribute('tabindex')) {
          heading.setAttribute('tabindex', '-1');
        }
        heading.focus({ preventScroll: true });
        /* Respect prefers-reduced-motion for scroll behaviour. */
        var prefersReduced = window.matchMedia &&
          window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        target.scrollIntoView({
          behavior: prefersReduced ? 'instant' : 'smooth',
          block: 'start',
        });
        return;
      }
      el = el.parentElement;
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    revealAnchor(window.location.hash);
  });

  window.addEventListener('hashchange', function () {
    revealAnchor(window.location.hash);
  });
}());

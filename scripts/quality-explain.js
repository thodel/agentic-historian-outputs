/* quality-explain.js — issue #111
 * Delegated click handler for .quality-explain-btn toggle buttons.
 *
 * Each button must have:
 *   - type="button"              — avoids accidental form submission
 *   - aria-expanded="false"      — initial collapsed state
 *   - aria-controls="<block-id>" — points at the matching explanation <div>
 *
 * On click the handler:
 *   - flips aria-expanded between "true" and "false"
 *   - removes (expanded) or adds (collapsed) the hidden attribute on the
 *     target element so non-CSS environments also respond correctly
 *
 * Keyboard-accessible by default: native <button> elements receive focus and
 * respond to Enter / Space without any extra handling.
 *
 * Event delegation is used so buttons inside dynamically-rendered content
 * (e.g. content loaded after DOMContentLoaded) are also handled.
 */
(function () {
  'use strict';

  /**
   * Toggle one explanation button + its target region.
   *
   * @param {Element} btn  A .quality-explain-btn button element.
   */
  function toggle(btn) {
    var targetId = btn.getAttribute('aria-controls');
    if (!targetId) return;
    var target = document.getElementById(targetId);
    if (!target) return;

    var expanded = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    if (expanded) {
      target.setAttribute('hidden', '');
    } else {
      target.removeAttribute('hidden');
    }
  }

  /**
   * Delegated click handler — find the closest .quality-explain-btn ancestor
   * of the clicked element (handles clicks on the icon span inside the button).
   *
   * @param {MouseEvent} event
   */
  function handleClick(event) {
    var btn = event.target.closest('.quality-explain-btn');
    if (!btn) return;
    toggle(btn);
  }

  document.addEventListener('click', handleClick);

  /* Export internals for unit testing. */
  if (typeof globalThis !== 'undefined') {
    globalThis.AgenticQualityExplain = { toggle: toggle, handleClick: handleClick };
  }
}());

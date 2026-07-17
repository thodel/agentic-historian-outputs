// Progressive recognition switching. Without JavaScript all <details> remain usable.
(() => {
  const viewers = [...document.querySelectorAll("[data-recognition-viewer]")];
  if (!viewers.length) return;

  const requested = () => new URL(window.location.href).searchParams.get("rec") || "selected";

  function syncPrimaryDownload(viewer, target) {
    const button = viewer.querySelector("[data-rec-primary-download]");
    const download = target.querySelector(".rec-download");
    if (!button) return;
    if (download) {
      button.hidden = false;
      button.href = download.href;
      button.setAttribute("download", download.getAttribute("download") || "");
    } else {
      button.hidden = true;
    }
  }

  function select(viewer, id, { push = false, focus = false } = {}) {
    const panels = [...viewer.querySelectorAll("[data-recognition-panel]")];
    const links = [...viewer.querySelectorAll("[data-recognition-select]")];
    const target = panels.find(panel => panel.dataset.recognitionPanel === id) ||
      panels.find(panel => panel.dataset.recognitionPanel === "selected") || panels[0];
    if (!target) return;
    for (const panel of panels) {
      const active = panel === target;
      panel.hidden = !active;
      panel.open = active;
    }
    for (const link of links) {
      if (link.dataset.recognitionSelect === target.dataset.recognitionPanel) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    }
    if (push) {
      const url = new URL(window.location.href);
      url.searchParams.set("rec", target.dataset.recognitionPanel);
      if (target.dataset.page) url.searchParams.set("page", target.dataset.page);
      else url.searchParams.delete("page");
      url.hash = target.id;
      history.pushState({ rec: target.dataset.recognitionPanel }, "", url);
    }
    if (focus) target.querySelector("summary")?.focus();
    syncPrimaryDownload(viewer, target);
    viewer.dispatchEvent(new CustomEvent("recognitionchange", { bubbles: true, detail: {
      id: target.dataset.recognitionPanel,
      page: target.dataset.page || "",
      engine: target.dataset.engine || "",
      model: target.dataset.model || "",
    }}));
  }

  for (const viewer of viewers) {
    viewer.classList.add("rec-viewer--enhanced");
    viewer.addEventListener("click", event => {
      const link = event.target.closest("[data-recognition-select]");
      if (!link || !viewer.contains(link)) return;
      event.preventDefault();
      select(viewer, link.dataset.recognitionSelect, { push: true, focus: true });
    });
    select(viewer, requested());
  }
  addEventListener("popstate", () => {
    for (const viewer of viewers) select(viewer, requested());
  });
})();


// ---- #8/#9 side-by-side comparison shell ----
// Supports: independent left/right selection, URL query params, back/forward nav,
// swap panes, keyboard accessibility, cross-page restriction.
(() => {
  const compares = [...document.querySelectorAll("[data-recognition-compare]")];
  if (!compares.length) return;

  // ── URL param helpers ──────────────────────────────────────────────
  const COMPARE_PARAM = "cmp";   // ?cmp=left-id:right-id  (empty string = not comparing)
  const PAGE_PARAM    = "page";  // already used by viewer, we read it here

  function readcmp() {
    const raw = new URL(window.location.href).searchParams.get(COMPARE_PARAM) || "";
    const [left, right] = raw.split(":");
    return { left: left || "", right: right || "" };
  }

  function pushcmp(leftId, rightId) {
    const url = new URL(window.location.href);
    const page = new URL(window.location.href).searchParams.get(PAGE_PARAM) || "";
    if (leftId || rightId) {
      url.searchParams.set(COMPARE_PARAM, `${leftId}:${rightId}`);
    } else {
      url.searchParams.delete(COMPARE_PARAM);
    }
    if (page) url.searchParams.set(PAGE_PARAM, page);
    history.pushState({ cmp: `${leftId}:${rightId}` }, "", url);
  }

  function getAllOptions(select) {
    return [...select.options].map(o => ({
      value: o.value,
      page:   o.dataset.page || "",
      disabled: o.disabled,
    }));
  }

  // ── Core helpers ───────────────────────────────────────────────────
  function candidateHTML(candidates, id) {
    const c = candidates.find(x => x.dataset.recognitionPanel === id) ||
              candidates.find(x => x.dataset.recognitionPanel === "selected");
    if (!c) return '<p class="notice notice--warning">Keine Version gewählt.</p>';
    const err = c.querySelector(".rec-error");
    if (err) return err.outerHTML;
    const meta = c.querySelector(".rec-meta");
    const pre  = c.querySelector(".rec-text");
    return (meta ? meta.outerHTML : "") + (pre ? pre.outerHTML : "");
  }

  function restrictSelects(leftSelect, rightSelect) {
    // Read the actual current page of each select's chosen option
    const leftPage  = leftSelect .options[leftSelect .selectedIndex]?.dataset.page || "";
    const rightPage = rightSelect.options[rightSelect.selectedIndex]?.dataset.page || "";
    for (const sel of [leftSelect, rightSelect]) {
      const otherPage = sel === leftSelect ? rightPage : leftPage;
      for (const opt of sel.options) {
        const optPage = opt.dataset.page || "";
        // Disable if other page is set, this page is set, and they differ
        opt.disabled = (otherPage !== "" && optPage !== "" && optPage !== otherPage);
      }
    }
  }

  function openOverlay(wrap) {
    const panesEl  = wrap.querySelector("[data-rec-compare-panes]");
    const openBtn  = wrap.querySelector("[data-rec-compare-open]");
    panesEl.hidden = false;
    openBtn?.setAttribute("aria-expanded", "true");
    // Focus first body so screen readers land in the right place
    wrap.querySelector("[data-rec-compare-body]")?.focus();
  }

  function closeOverlay(wrap) {
    const panesEl = wrap.querySelector("[data-rec-compare-panes]");
    const openBtn = wrap.querySelector("[data-rec-compare-open]");
    panesEl.hidden = true;
    openBtn?.setAttribute("aria-expanded", "false");
    openBtn?.focus();
  }

  // ── Pane update ────────────────────────────────────────────────────
  function updatePane(pane, candidates, selectEl) {
    const body = pane.querySelector("[data-rec-compare-body]");
    if (!body) return;
    body.innerHTML = candidateHTML(candidates, selectEl.value);
    pane.dataset.recCompareSelected = selectEl.value;
  }

  // ── Main init per compare widget ───────────────────────────────────
  for (const wrap of compares) {
    const leftPane   = wrap.querySelector("[data-rec-compare-pane='left']");
    const rightPane  = wrap.querySelector("[data-rec-compare-pane='right']");
    const leftSel    = wrap.querySelector("[data-rec-compare-select='left']");
    const rightSel   = wrap.querySelector("[data-rec-compare-select='right']");
    const openBtn    = wrap.querySelector("[data-rec-compare-open]");
    const closeBtn   = wrap.querySelector("[data-rec-compare-close]");
    const swapBtn    = wrap.querySelector("[data-rec-compare-swap]");
    const panesEl    = wrap.querySelector("[data-rec-compare-panes]");
    if (!leftPane || !rightPane || !leftSel || !rightSel) continue;

    const viewer    = wrap.closest("[data-recognition-viewer]");
    const allPanels = viewer
      ? [...viewer.querySelectorAll("[data-recognition-panel]")]
      : [];

    // Build swap button dynamically if not in HTML (issue #9 requirement)
    if (swapBtn) swapBtn.remove(); // remove placeholder if any
    const swapInserted = wrap.querySelector("[data-rec-compare-swap]");
    const generatedSwap = !swapInserted;

    // ── Initial state from URL or defaults ───────────────────────
    const { left: urlLeft, right: urlRight } = readcmp();
    // Select options in selects to match URL (or fall back to defaults)
    if (urlLeft  && [...leftSel.options].some(o => o.value === urlLeft  && !o.disabled)) leftSel.value  = urlLeft;
    if (urlRight && [...rightSel.options].some(o => o.value === urlRight && !o.disabled)) rightSel.value = urlRight;
    // If no URL, use HTML defaults (already set by server as selected= attributes)

    restrictSelects(leftSel, rightSel);
    updatePane(leftPane,  allPanels, leftSel);
    updatePane(rightPane, allPanels, rightSel);

    // Show overlay if cmp param is present
    if (urlLeft || urlRight) openOverlay(wrap);

    // ── Keyboard: Enter on Vergleichen button ───────────────────
    openBtn?.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openOverlay(wrap); }
    });

    // ── Open ────────────────────────────────────────────────────
    openBtn?.addEventListener("click", () => {
      openOverlay(wrap);
      pushcmp(leftSel.value, rightSel.value);
    });

    // ── Close ───────────────────────────────────────────────────
    closeBtn?.addEventListener("click", () => {
      closeOverlay(wrap);
      pushcmp("", "");
    });

    // ── Swap ────────────────────────────────────────────────────
    if (generatedSwap) {
      // Inject swap button between the two panes in the DOM
      const swapEl = document.createElement("button");
      swapEl.setAttribute("class", "btn-rec-compare btn-rec-compare-swap");
      swapEl.setAttribute("type", "button");
      swapEl.setAttribute("data-rec-compare-swap", "");
      swapEl.setAttribute("aria-label", "Links und rechts tauschen");
      swapEl.textContent = "\u21c4"; // ℆ horizontal swap arrow
      panesEl.insertBefore(swapEl, rightPane);
    }

    const injectedSwap = wrap.querySelector("[data-rec-compare-swap]") || swapBtn;
    injectedSwap?.addEventListener("click", () => {
      const tmp = leftSel.value;
      leftSel.value  = rightSel.value;
      rightSel.value = tmp;
      updatePane(leftPane,  allPanels, leftSel);
      updatePane(rightPane, allPanels, rightSel);
      restrictSelects(leftSel, rightSel);
      pushcmp(leftSel.value, rightSel.value);
    });

    // ── Select changes ──────────────────────────────────────────
    function onSelectChange(sel, pane) {
      updatePane(pane, allPanels, sel);
      restrictSelects(leftSel, rightSel);
      pushcmp(leftSel.value, rightSel.value);
    }

    leftSel .addEventListener("change", () => onSelectChange(leftSel,  leftPane));
    rightSel.addEventListener("change", () => onSelectChange(rightSel, rightPane));

    // ── ESC to close ─────────────────────────────────────────────
    panesEl.addEventListener("keydown", e => {
      if (e.key === "Escape") { e.stopPropagation(); closeOverlay(wrap); pushcmp("", ""); }
    });

    // ── Back/forward: restore comparison state ───────────────────
    addEventListener("popstate", () => {
      const { left, right } = readcmp();
      if (!left && !right) { closeOverlay(wrap); return; }
      // Restore select values
      if ([...leftSel.options].some(o => o.value === left  && !o.disabled)) leftSel.value  = left;
      if ([...rightSel.options].some(o => o.value === right && !o.disabled)) rightSel.value = right;
      restrictSelects(leftSel, rightSel);
      updatePane(leftPane,  allPanels, leftSel);
      updatePane(rightPane, allPanels, rightSel);
      openOverlay(wrap);
    });
    // ── Scroll synchronisation (#10) ────────────────────────────
    const leftBody  = leftPane .querySelector("[data-rec-compare-body]");
    const rightBody = rightPane.querySelector("[data-rec-compare-body]");
    if (leftBody && rightBody) {
      let syncEnabled = true;
      let isScrolling = false;  // guard against recursive events

      // Inject the sync toggle button beside the close button
      const syncToggle = document.createElement("button");
      syncToggle.setAttribute("class", "btn-rec-compare btn-rec-compare-sync");
      syncToggle.setAttribute("type", "button");
      syncToggle.setAttribute("data-rec-compare-sync-toggle", "");
      syncToggle.setAttribute("aria-pressed", "true");
      syncToggle.setAttribute("aria-label", "Scroll-Synchronisation deaktivieren");
      syncToggle.textContent = "\u21c4\uFE0e"; // sync icon with variation selector
      panesEl.appendChild(syncToggle);

      function applyProportionalScroll(source, target) {
        if (!syncEnabled) return;
        const sourceEl  = source;
        const targetEl  = target;
        const sourceMax = sourceEl.scrollHeight - sourceEl.clientHeight;
        const targetMax = targetEl.scrollHeight - targetEl.clientHeight;
        if (sourceMax <= 0 || targetMax <= 0) return;
        const ratio  = sourceEl.scrollTop / sourceMax;
        targetEl.scrollTop = Math.round(ratio * targetMax);
      }

      leftBody.addEventListener("scroll", () => {
        if (isScrolling) return;
        isScrolling = true;
        requestAnimationFrame(() => {
          applyProportionalScroll(leftBody, rightBody);
          isScrolling = false;
        });
      });

      rightBody.addEventListener("scroll", () => {
        if (isScrolling) return;
        isScrolling = true;
        requestAnimationFrame(() => {
          applyProportionalScroll(rightBody, leftBody);
          isScrolling = false;
        });
      });

      syncToggle.addEventListener("click", () => {
        syncEnabled = !syncEnabled;
        syncToggle.setAttribute("aria-pressed", String(syncEnabled));
        syncToggle.setAttribute("aria-label",
          syncEnabled
            ? "Scroll-Synchronisation deaktivieren"
            : "Scroll-Synchronisation aktivieren");
        syncToggle.style.opacity = syncEnabled ? "1" : "0.45";
      });

      // Respect prefers-reduced-motion: disable sync by default
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        syncEnabled = false;
        syncToggle.style.opacity = "0.45";
        syncToggle.setAttribute("aria-pressed", "false");
        syncToggle.setAttribute("aria-label", "Scroll-Synchronisation aktivieren");
      }
    }

  }
})();

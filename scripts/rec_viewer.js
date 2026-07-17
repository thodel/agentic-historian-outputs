// Progressive recognition switching. Without JavaScript all <details> remain usable.
(() => {
  const viewers = [...document.querySelectorAll("[data-recognition-viewer]")];
  if (!viewers.length) return;

  const requested = () => new URL(window.location.href).searchParams.get("rec") || "selected";

  // Sync primary download button when active candidate changes (#35)
  function syncPrimaryDownload(viewer, targetPanelId) {
    const btn = viewer.querySelector("[data-rec-primary-download]");
    if (!btn) return;
    const panels = [...viewer.querySelectorAll("[data-recognition-panel]")];
    const panel = panels.find(p => p.dataset.recognitionPanel === targetPanelId) ||
      panels.find(p => p.dataset.recognitionPanel === "selected");
    if (!panel) return;
    const dl = panel.querySelector(".rec-download");
    const newHref = dl ? dl.getAttribute("href") : "";
    const filename = newHref.split("/").pop() || "transcription.txt";
    btn.setAttribute("href", newHref);
    btn.setAttribute("download", filename);
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
    syncPrimaryDownload(viewer, target.dataset.recognitionPanel);
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

// ---- #8 side-by-side comparison shell ----
(() => {
  const compares = [...document.querySelectorAll("[data-recognition-compare]")];
  if (!compares.length) return;

  // Build the display HTML for one candidate pane
  function candidateHTML(candidates, id) {
    const c = candidates.find(x => x.dataset.recognitionPanel === id) ||
              candidates.find(x => x.dataset.recognitionPanel === "selected");
    if (!c) return '<p class="notice notice--warning">Keine Version gewählt.</p>';
    const err = c.querySelector(".rec-error");
    if (err) return err.outerHTML;
    const meta = c.querySelector(".rec-meta");
    const pre = c.querySelector(".rec-text");
    return (meta ? meta.outerHTML : "") + (pre ? pre.outerHTML : "");
  }

  // Restrict each <select> to candidates on the same page as the other's value
  function restrictSelects(leftSelect, rightSelect) {
    const leftPage = leftSelect.options[leftSelect.selectedIndex]
      ?.dataset.page || "";
    const rightPage = rightSelect.options[rightSelect.selectedIndex]
      ?.dataset.page || "";
    for (const sel of [leftSelect, rightSelect]) {
      const otherPage = sel === leftSelect ? rightPage : leftPage;
      for (const opt of sel.options) {
        // An option is valid if its page matches the other's page, or both are empty
        const optPage = opt.dataset.page || "";
        opt.disabled = (otherPage !== "" && optPage !== "" && optPage !== otherPage);
      }
    }
  }

  // Initialise a pane body from the currently selected option in its <select>
  function initPane(pane, candidates) {
    const sel = pane.querySelector("[data-rec-compare-select]");
    if (!sel) return;
    pane.dataset.recCompareSelected = sel.value;
    const body = pane.querySelector("[data-rec-compare-body]");
    if (body) body.innerHTML = candidateHTML(candidates, sel.value);
  }

  for (const wrap of compares) {
    const leftPane = wrap.querySelector("[data-rec-compare-pane='left']");
    const rightPane = wrap.querySelector("[data-rec-compare-pane='right']");
    const leftSel = wrap.querySelector("[data-rec-compare-select='left']");
    const rightSel = wrap.querySelector("[data-rec-compare-select='right']");
    const panebutton = wrap.querySelector("[data-rec-compare-open]");
    const closebtn = wrap.querySelector("[data-rec-compare-close]");
    const panesEl = wrap.querySelector("[data-rec-compare-panes]");
    if (!leftPane || !rightPane || !leftSel || !rightSel) continue;

    // Collect all panel elements from the viewer sibling (same root)
    const viewer = wrap.closest("[data-recognition-viewer]");
    const allPanels = viewer
      ? [...viewer.querySelectorAll("[data-recognition-panel]")]
      : [];

    initPane(leftPane, allPanels);
    initPane(rightPane, allPanels);
    restrictSelects(leftSel, rightSel);

    panebutton?.addEventListener("click", () => {
      panesEl.hidden = false;
      panebutton.setAttribute("aria-expanded", "true");
    });

    closebtn?.addEventListener("click", () => {
      panesEl.hidden = true;
      panebutton?.setAttribute("aria-expanded", "false");
    });

    const handleSelect = (sel, pane) => {
      const body = pane.querySelector("[data-rec-compare-body]");
      if (body) body.innerHTML = candidateHTML(allPanels, sel.value);
      pane.dataset.recCompareSelected = sel.value;
      restrictSelects(leftSel, rightSel);
    };

    leftSel.addEventListener("change", () => handleSelect(leftSel, leftPane));
    rightSel.addEventListener("change", () => handleSelect(rightSel, rightPane));
  }
})();

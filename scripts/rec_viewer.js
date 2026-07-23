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
      updateDiff(leftSel.value, rightSel.value);
    });

    // ── Select changes ──────────────────────────────────────────
    function onSelectChange(sel, pane) {
      updatePane(pane, allPanels, sel);
      restrictSelects(leftSel, rightSel);
      pushcmp(leftSel.value, rightSel.value);
      updateDiff(leftSel.value, rightSel.value);
    }

    leftSel .addEventListener("change", () => onSelectChange(leftSel,  leftPane));
    rightSel.addEventListener("change", () => onSelectChange(rightSel, rightPane));

    // ── ESC to close ─────────────────────────────────────────────
    panesEl.addEventListener("keydown", e => {
      if (e.key === "Escape") { e.stopPropagation(); closeOverlay(wrap); pushcmp("", ""); }
    });

    // ── Back/forward: restore comparison state ───────────────────

  // ── #11 diff highlighting ──────────────────────────────────────
  const DIFF_DISABLED_ATTR = "data-rec-compare-diff-disabled";
  const MAX_DIFF_CHARS = 50_000;
  const MAX_DIFF_CELLS = 2_000_000;

  function escapeHTML(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // Word-level diff: returns array of {type, left, right}
  // type in "equal", "insert", "delete", "change"
  function wordLevelDiff(left, right) {
    const lWords = left.split(/(\s+)/);
    const rWords = right.split(/(\s+)/);
    const m = lWords.length, n = rWords.length;
    // Build DP table for LCS of words
    const dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        if (lWords[i-1] === rWords[j-1]) dp[i][j] = dp[i-1][j-1] + 1;
        else dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
      }
    }
    // Backtrack
    const pairs = [];
    let i = m, j = n;
    while (i > 0 || j > 0) {
      if (i > 0 && j > 0 && lWords[i-1] === rWords[j-1]) {
        pairs.unshift({type: "equal", left: lWords[i-1], right: rWords[j-1]});
        i--; j--;
      } else if (j > 0 && (i === 0 || dp[i][j-1] >= dp[i-1][j])) {
        pairs.unshift({type: "insert", left: "", right: rWords[j-1]});
        j--;
      } else {
        pairs.unshift({type: "delete", left: lWords[i-1], right: ""});
        i--;
      }
    }
    // Merge consecutive runs of the same type
    const merged = [];
    for (const p of pairs) {
      if (merged.length && merged[merged.length-1].type === p.type) {
        merged[merged.length-1].left  += p.left;
        merged[merged.length-1].right += p.right;
      } else {
        merged.push({...p});
      }
    }
    return merged;
  }

  function diffMarkType(type) {
    switch (type) {
      case "insert":  return "diff-insert";
      case "delete":  return "diff-delete";
      case "change":  return "diff-change";
      default:        return null;
    }
  }

  function diffLabel(type) {
    switch (type) {
      case "insert":  return "eingefügt";
      case "delete":  return "gelöscht";
      case "change":  return "geändert";
      default:        return null;
    }
  }

  function renderDiffHTML(pairs) {
    return pairs.map(p => {
      const cls = diffMarkType(p.type);
      if (!cls) return `<span>${escapeHTML(p.left)}</span>`;
      const label = diffLabel(p.type);
      return `<span class="${cls}" aria-label="${label}">` +
             `<span>${escapeHTML(p.left)}</span>` +
             (p.type !== "delete" ? `<span>${escapeHTML(p.right)}</span>` : "") +
             `</span>`;
    }).join("");
  }

  // Find plain text from candidate panel
  function extractText(candidates, id) {
    const c = candidates.find(x => x.dataset.recognitionPanel === id) ||
              candidates.find(x => x.dataset.recognitionPanel === "selected");
    if (!c) return null;
    const pre = c.querySelector(".rec-text");
    return pre ? pre.textContent : null;
  }

  function diffContent(leftText, rightText) {
    if (leftText === null || rightText === null) {
      return `<p class="notice notice--warning">Version nicht verfügbar.</p>`;
    }
    const max = Math.max(leftText.length, rightText.length);
    if (max > MAX_DIFF_CHARS) {
      return `<p class="notice">Diff für sehr lange Texte (${max} Zeichen) nicht verfügbar. ` +
             `Zum Vergleichen bitte kürzere Versionen wählen.</p>`;
    }
    const cells = leftText.split(/\s+/).length * rightText.split(/\s+/).length;
    if (cells > MAX_DIFF_CELLS) {
      return `<p class="notice">Diff für diese langen Texte ist zu aufwendig. ` +
             `Zum Vergleichen bitte kürzere Versionen wählen.</p>`;
    }
    if (leftText.trim() === rightText.trim()) {
      return `<p class="notice">Die beiden Versionen sind identisch.</p>`;
    }
    const pairs = wordLevelDiff(leftText, rightText);
    // Detect change: equal words on one side, insert+delete on other = "change"
    const simplified = pairs.map(p => {
      // If left and right are both non-empty and different, mark as "change"
      if (p.type !== "equal" && p.left && p.right) {
        return {type: "change", left: p.left, right: p.right};
      }
      return p;
    });
    return renderDiffHTML(simplified);
  }

  // ── Inject diff toggle button ──────────────────────────────────
  // Find or create the diff toggle button in the pane toolbar
  function ensureDiffToggle(pane) {
    if (pane.querySelector("[data-rec-compare-diff-toggle]")) return;
    const btn = document.createElement("button");
    btn.setAttribute("class", "btn-rec-compare btn-rec-compare-diff");
    btn.setAttribute("type", "button");
    btn.setAttribute("data-rec-compare-diff-toggle", "");
    btn.setAttribute("aria-pressed", "false");
    btn.setAttribute("aria-label", "Unterschiede hervorheben");
    btn.textContent = "\u2194"; // horizontal arrow ↔
    // Insert after the sync toggle if present, else append
    const syncToggle = pane.querySelector("[data-rec-compare-sync-toggle]");
    if (syncToggle) syncToggle.insertAdjacentElement("afterend", btn);
    else pane.appendChild(btn);
  }

  // Create diff region between the two panes
  function ensureDiffRegion() {
    if (wrap.querySelector("[data-rec-compare-diff]")) return wrap.querySelector("[data-rec-compare-diff]");
    const el = document.createElement("div");
    el.setAttribute("class", "rec-compare-diff");
    el.setAttribute("data-rec-compare-diff", "");
    el.setAttribute("role", "region");
    el.setAttribute("aria-label", "Unterschiede");
    el.hidden = true;
    // Insert after the panes, before the close button toolbar
    const toolbar = wrap.querySelector(".rec-compare-toolbar");
    if (toolbar) toolbar.insertAdjacentElement("afterend", el);
    else panesEl.insertBefore(el, panesEl.querySelector("[data-rec-compare-pane='right']")?.nextSibling);
    return el;
  }

  function updateDiff(leftSelVal, rightSelVal) {
    const diffEl  = wrap.querySelector("[data-rec-compare-diff]");
    const toggle  = wrap.querySelector("[data-rec-compare-diff-toggle]");
    if (!diffEl) return;
    const disabled = diffEl.hasAttribute(DIFF_DISABLED_ATTR);
    if (disabled) { diffEl.hidden = true; return; }
    const leftText  = extractText(allPanels, leftSelVal);
    const rightText = extractText(allPanels, rightSelVal);
    diffEl.innerHTML = diffContent(leftText, rightText);
    diffEl.hidden = false;
  }

  // Inject toggle into each pane header
  ensureDiffToggle(leftPane);
  ensureDiffToggle(rightPane);
  const diffEl = ensureDiffRegion();
  diffEl.setAttribute(DIFF_DISABLED_ATTR, "");
  diffEl.hidden = true;

  // Diff toggle button
  for (const btn of wrap.querySelectorAll("[data-rec-compare-diff-toggle]")) {
    btn.addEventListener("click", () => {
      const diffRegion = wrap.querySelector("[data-rec-compare-diff]");
      if (!diffRegion) return;
      const isDisabled = diffRegion.hasAttribute(DIFF_DISABLED_ATTR);
      if (isDisabled) {
        diffRegion.removeAttribute(DIFF_DISABLED_ATTR);
        btn.setAttribute("aria-pressed", "true");
        btn.setAttribute("aria-label", "Unterschiede hervorheben");
        updateDiff(leftSel.value, rightSel.value);
      } else {
        diffRegion.setAttribute(DIFF_DISABLED_ATTR, "");
        diffRegion.hidden = true;
        btn.setAttribute("aria-pressed", "false");
        btn.setAttribute("aria-label", "Unterschiede anzeigen");
      }
    });
  }

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

(() => {
  const viewers = [...document.querySelectorAll("[data-recognition-viewer]")];
  if (!viewers.length) return;

  const selectionFromUrl = () => {
    const url = new URL(window.location.href);
    return url.searchParams.get("recognition") || "selected";
  };

  const select = (viewer, id, { updateUrl = false, focus = false } = {}) => {
    const links = [...viewer.querySelectorAll("[data-recognition-select]")];
    const panels = [...viewer.querySelectorAll("[data-recognition-panel]")];
    const target = panels.find(panel => panel.dataset.recognitionPanel === id) ||
      panels.find(panel => panel.dataset.recognitionPanel === "selected") || panels[0];
    if (!target) return;

    for (const panel of panels) {
      const active = panel === target;
      panel.hidden = !active;
      panel.open = active;
    }
    for (const link of links) {
      const active = link.dataset.recognitionSelect === target.dataset.recognitionPanel;
      if (active) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    }

    if (updateUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set("recognition", target.dataset.recognitionPanel);
      if (target.dataset.page) url.searchParams.set("page", target.dataset.page);
      else url.searchParams.delete("page");
      url.hash = target.id;
      window.history.pushState({ recognition: target.dataset.recognitionPanel }, "", url);
    }
    if (focus) target.querySelector("summary")?.focus();
  };

  for (const viewer of viewers) {
    viewer.classList.add("recognition-viewer--enhanced");
    viewer.addEventListener("click", event => {
      const link = event.target.closest("[data-recognition-select]");
      if (!link || !viewer.contains(link)) return;
      event.preventDefault();
      select(viewer, link.dataset.recognitionSelect, { updateUrl: true, focus: true });
    });
    select(viewer, selectionFromUrl());
  }

  window.addEventListener("popstate", () => {
    for (const viewer of viewers) select(viewer, selectionFromUrl());
  });
})();

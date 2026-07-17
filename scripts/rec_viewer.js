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

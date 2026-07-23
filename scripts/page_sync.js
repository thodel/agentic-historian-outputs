// Keep source pages and page-attributed recognition candidates in one URL-backed state.
(() => {
  function chooseCandidate(links, page, preferred = {}) {
    const pageLinks = links.filter(link => link.dataset.page === page);
    return pageLinks.find(link => link.dataset.engine === preferred.engine &&
      link.dataset.model === preferred.model) || pageLinks[0] || null;
  }
  globalThis.AgenticPageSync = { chooseCandidate };
  if (typeof document === "undefined") return;

  for (const workspace of document.querySelectorAll("[data-evidence-workspace]")) {
    const viewer = workspace.querySelector("[data-evidence-viewer]");
    const recViewer = workspace.querySelector("[data-recognition-viewer]");
    const warning = workspace.querySelector("[data-page-sync-warning]");
    const buttons = [...workspace.querySelectorAll("[data-source-page]")];
    const links = recViewer ? [...recViewer.querySelectorAll("[data-recognition-select]")] : [];
    const payloadNode = workspace.querySelector("[data-source-reference]");
    let pages = [];
    let preferred = {};
    try { pages = JSON.parse(payloadNode?.textContent || "{}").pages || []; } catch (_) { /* invalid payload */ }
    if (!buttons.length) continue;

    const mapping = page => pages.find(item => item.page === page);
    const showWarning = message => {
      warning.hidden = !message;
      warning.textContent = message;
    };
    const setButton = page => {
      for (const button of buttons) button.setAttribute("aria-current", button.dataset.sourcePage === page ? "page" : "false");
    };
    const moveSource = page => {
      const match = mapping(page);
      setButton(page);
      if (!match) {
        showWarning(`Für die Erkennungsseite „${page}“ ist kein Digitalisat zugeordnet.`);
        return false;
      }
      showWarning("");
      viewer.dispatchEvent(new CustomEvent("evidencepagechange", { detail: {
        page, canvasUrl: match.canvas_url || "", imageUrl: match.image_url || "",
      }}));
      return true;
    };
    const updateUrlPage = page => {
      const url = new URL(window.location.href);
      url.searchParams.set("page", page);
      history.replaceState(history.state, "", url);
    };

    for (const button of buttons) button.addEventListener("click", () => {
      const page = button.dataset.sourcePage;
      moveSource(page);
      const candidate = chooseCandidate(links, page, preferred);
      if (candidate) candidate.click();
      else {
        updateUrlPage(page);
        showWarning(`Für die Quellenseite „${page}“ ist keine Erkennung zugeordnet.`);
      }
    });

    recViewer?.addEventListener("recognitionchange", event => {
      const { page, engine, model } = event.detail;
      if (engine || model) preferred = { engine, model };
      if (page) moveSource(page);
    });

    const requested = new URL(window.location.href).searchParams.get("page");
    const initial = requested || buttons[0].dataset.sourcePage;
    moveSource(initial);
    if (requested) {
      const candidate = chooseCandidate(links, requested, preferred);
      if (candidate && !candidate.matches('[aria-current="true"]')) candidate.click();
    }
    addEventListener("popstate", () => {
      const page = new URL(window.location.href).searchParams.get("page");
      if (page) moveSource(page);
    });
  }
})();

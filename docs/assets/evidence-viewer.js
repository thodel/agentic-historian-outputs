// Dependency-free IIIF/direct-image evidence viewer.
(() => {
  function identifier(value) {
    return value && (value.id || value["@id"] || "");
  }

  function iiifImageUrl(manifest, canvasId = "") {
    const canvases = manifest?.items || manifest?.sequences?.[0]?.canvases || [];
    const canvas = canvases.find(item => identifier(item) === canvasId) || canvases[0];
    const body = canvas?.items?.[0]?.items?.[0]?.body || canvas?.images?.[0]?.resource;
    if (!body) return "";
    const direct = identifier(body);
    if (direct) return direct;
    const service = Array.isArray(body.service) ? body.service[0] : body.service;
    const serviceId = identifier(service);
    return serviceId ? `${serviceId.replace(/\/$/, "")}/full/max/0/default.jpg` : "";
  }

  globalThis.AgenticEvidenceViewer = { iiifImageUrl };
  if (typeof document === "undefined") return;

  for (const viewer of document.querySelectorAll("[data-evidence-viewer]")) {
    const image = viewer.querySelector("[data-evidence-image]");
    const stage = viewer.querySelector("[data-evidence-stage]");
    const status = viewer.querySelector("[data-evidence-status]");
    const sourceUrl = viewer.dataset.sourceUrl;
    let zoom = 1;
    let manifestPromise;

    const announce = message => { status.textContent = message; };
    const applyZoom = value => {
      zoom = Math.min(4, Math.max(.5, value));
      image.style.width = `${zoom * 100}%`;
      viewer.querySelector("[data-evidence-zoom]").textContent = `${Math.round(zoom * 100)}%`;
    };
    const show = url => {
      if (!url) throw new Error("missing image");
      image.addEventListener("load", () => {
        image.hidden = false;
        announce("Digitalisat geladen.");
      }, { once: true });
      image.addEventListener("error", () => {
        image.hidden = true;
        announce("Das Digitalisat konnte nicht geladen werden. Öffnen Sie die Originalquelle.");
      }, { once: true });
      image.src = url;
    };

    viewer.addEventListener("click", event => {
      const action = event.target.closest("[data-evidence-action]")?.dataset.evidenceAction;
      if (action === "zoom-in") applyZoom(zoom + .25);
      if (action === "zoom-out") applyZoom(zoom - .25);
      if (action === "reset") { applyZoom(1); stage.scrollTo({ top: 0, left: 0 }); }
      if (action === "fullscreen") stage.requestFullscreen?.();
    });

    applyZoom(1);
    function load(detail = {}) {
      announce("Digitalisat wird geladen …");
      if (detail.imageUrl) { show(detail.imageUrl); return; }
      if (viewer.dataset.sourceType === "image") { show(sourceUrl); return; }
      if (!manifestPromise) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 12000);
      manifestPromise = fetch(sourceUrl, { signal: controller.signal, credentials: "omit" })
        .then(response => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .finally(() => clearTimeout(timeout));
      }
      manifestPromise
        .then(manifest => show(iiifImageUrl(manifest, detail.canvasUrl || "")))
        .catch(() => announce("Das IIIF-Manifest konnte nicht geladen werden. Öffnen Sie die Originalquelle."));
    }
    viewer.addEventListener("evidencepagechange", event => load(event.detail));
    load();
  }
})();

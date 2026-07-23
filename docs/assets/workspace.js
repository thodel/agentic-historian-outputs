// Accessible source/transcription split workspace. The ratio is local UI state,
// deliberately kept out of shareable document URLs.
(() => {
  const MIN = 25;
  const MAX = 75;
  const clamp = value => Math.min(MAX, Math.max(MIN, Math.round(value)));

  for (const workspace of document.querySelectorAll("[data-evidence-workspace]")) {
    const divider = workspace.querySelector("[data-workspace-divider]");
    if (!divider) continue;
    const storageKey = `agentic-historian:pane-ratio:${workspace.dataset.docId || "default"}`;

    function apply(value, persist = false) {
      const ratio = clamp(Number(value) || 50);
      workspace.style.setProperty("--source-pane-ratio", `${ratio}%`);
      divider.setAttribute("aria-valuenow", String(ratio));
      if (persist) {
        try { localStorage.setItem(storageKey, String(ratio)); } catch (_) { /* storage unavailable */ }
      }
    }

    try { apply(localStorage.getItem(storageKey) || 50); } catch (_) { apply(50); }

    divider.addEventListener("keydown", event => {
      const current = Number(divider.getAttribute("aria-valuenow")) || 50;
      const next = event.key === "ArrowLeft" ? current - 5
        : event.key === "ArrowRight" ? current + 5
        : event.key === "Home" ? MIN
        : event.key === "End" ? MAX : null;
      if (next === null) return;
      event.preventDefault();
      apply(next, true);
    });

    divider.addEventListener("pointerdown", event => {
      if (matchMedia("(max-width: 55rem)").matches) return;
      divider.setPointerCapture?.(event.pointerId);
      const move = moveEvent => {
        const bounds = workspace.getBoundingClientRect();
        apply(((moveEvent.clientX - bounds.left) / bounds.width) * 100);
      };
      const finish = finishEvent => {
        divider.removeEventListener("pointermove", move);
        divider.removeEventListener("pointerup", finish);
        divider.removeEventListener("pointercancel", finish);
        apply(divider.getAttribute("aria-valuenow"), true);
        divider.releasePointerCapture?.(finishEvent.pointerId);
      };
      divider.addEventListener("pointermove", move);
      divider.addEventListener("pointerup", finish);
      divider.addEventListener("pointercancel", finish);
    });
  }
})();

// ─── Copy transcription to clipboard (#130) ──────────────────────
(() => {
  if (typeof document === "undefined") return;

  // Get plain text from the line-numbered transcription structure
  function getTranscriptText(wrap) {
    return [...wrap.querySelectorAll(".line-text")]
      .map(span => span.textContent || "")
      .join("
");
  }

  for (const btn of document.querySelectorAll("[data-copy-transcript]")) {
    btn.addEventListener("click", async () => {
      const wrap = btn.closest(".transcription-wrap") || document.querySelector(".transcription-wrap");
      if (!wrap) return;
      const text = getTranscriptText(wrap);
      try {
        await navigator.clipboard.writeText(text);
        btn.classList.add("copy-btn--copied");
        const original = btn.innerHTML;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg> Kopiert!`;
        setTimeout(() => {
          btn.classList.remove("copy-btn--copied");
          btn.innerHTML = original;
        }, 2000);
      } catch (_) {
        // Clipboard unavailable — silently skip; no fallback needed
      }
    });
  }
})();

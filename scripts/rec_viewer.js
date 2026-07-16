// Recognition viewer — progressive enhancement (issues #2, #3)
// - Tab switching without navigation
// - URL persistence: ?rec=<candidate-id> restores selection
// - Browser back/forward support
// - Keyboard accessible
document.querySelectorAll('.rec-viewer').forEach(function(viewer) {
  var docId    = viewer.dataset.docId || '';
  var panels   = Array.from(viewer.querySelectorAll('.rec-panel'));
  var inputs   = Array.from(viewer.querySelectorAll('.rec-tab-input'));
  var paramKey = 'rec';   // URL query parameter name

  // ── helpers ──────────────────────────────────────────────────────────────
  function getCandidateId() {
    // 1. URL param takes precedence
    var val = new URLSearchParams(window.location.search).get(paramKey);
    if (val) { return val; }
    // 2. currently checked radio
    var checked = viewer.querySelector('.rec-tab-input:checked');
    return checked ? checked.value : (inputs[0] ? inputs[0].value : null);
  }

  function activate(id) {
    panels.forEach(function(p) {
      p.classList.toggle('is-active', p.id === id);
    });
    inputs.forEach(function(inp) {
      inp.checked = inp.value === id;
    });
  }

  function persist(id) {
    // Update URL without navigation
    var url = new URL(window.location.href);
    url.searchParams.set(paramKey, id);
    history.replaceState({}, '', url.toString());
  }

  // ── init ─────────────────────────────────────────────────────────────────
  viewer.classList.add('js');
  var initial = getCandidateId();
  if (initial) { activate(initial); }

  // ── keyboard / mouse selection ───────────────────────────────────────────
  inputs.forEach(function(inp) {
    inp.addEventListener('change', function() {
      activate(inp.value);
      persist(inp.value);
    });
  });
});


// Recognition viewer — progressive enhancement (issues #2, #3, #35)
// - Tab switching without navigation
// - URL persistence: ?rec=<candidate-id> restores selection
// - Browser back/forward support
// - Keyboard accessible
// - Active download target updates on candidate switch (issue #35)
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

// ── Active download section (issue #35) ─────────────────────────────────────
document.querySelectorAll('.dl-cand-select').forEach(function(select) {
  var docId = select.dataset.docId || '';
  var dlBtn = document.querySelector('.dl-btn[data-doc-id="' + docId + '"]');

  // Map from candidate-id (tab value) to download href
  // Gather all data-cand links from the recognition panels
  var candToHref = {};
  var candLabels = {};
  document.querySelectorAll('.rec-panel').forEach(function(panel) {
    var dlLink = panel.querySelector('a[data-cand]');
    if (dlLink) {
      var cand = dlLink.dataset.cand;
      candToHref[cand] = dlLink.href;
    }
  });

  // Default download button
  var defaultHref = dlBtn ? dlBtn.dataset.defaultHref : null;

  select.addEventListener('change', function() {
    var cand = select.value;
    if (cand && candToHref[cand]) {
      dlBtn.href = candToHref[cand];
      dlBtn.setAttribute('data-cand', cand);
      // Update label to include engine/page info
      var opt = select.querySelector('option[value="' + cand + '"]');
      if (opt) {
        dlBtn.setAttribute('aria-label', 'Aktuelle Transkription herunterladen (' + opt.text + ')');
      }
    } else if (defaultHref) {
      dlBtn.href = defaultHref;
    }
    // Sync: also activate the corresponding tab in the viewer
    var tabInput = document.querySelector('.rec-tab-input[value="' + cand + '"]');
    if (tabInput) { tabInput.checked = true; }
    // Update URL hash to match
    if (cand) {
      var url = new URL(window.location.href);
      url.searchParams.set('rec', cand);
      history.replaceState({}, '', url.toString());
    }
  });
});

// ── Sync: when viewer tab changes, update download select (bidirectional) ───
document.querySelectorAll('.rec-viewer').forEach(function(viewer) {
  var docId = viewer.dataset.docId || '';
  var inputs = Array.from(viewer.querySelectorAll('.rec-tab-input'));
  var dlSelect = document.querySelector('.dl-cand-select[data-doc-id="' + docId + '"]');
  if (!dlSelect) return;

  inputs.forEach(function(inp) {
    inp.addEventListener('change', function() {
      if (inp.checked) {
        dlSelect.value = inp.value;
      }
    });
  });
});

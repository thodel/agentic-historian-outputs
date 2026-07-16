<script>
// Recognition viewer: progressive enhancement
document.querySelectorAll('.rec-viewer').forEach(function(viewer) {
  viewer.classList.add('js');
  var panels = viewer.querySelectorAll('.rec-panel');
  function showPanel(id) {
    panels.forEach(function(p) {
      p.classList.toggle('is-active', p.id === id);
    });
  }
  var checked = viewer.querySelector('.rec-tab-input:checked');
  if (checked) { showPanel(checked.value); }
  viewer.querySelectorAll('.rec-tab-input').forEach(function(inp) {
    inp.addEventListener('change', function() { showPanel(inp.value); });
  });
});

</script>

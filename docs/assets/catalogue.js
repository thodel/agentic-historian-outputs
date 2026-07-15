(() => {
  const search = document.querySelector("#catalogue-search");
  const filter = document.querySelector("#catalogue-filter");
  const cards = [...document.querySelectorAll(".catalogue-card")];
  const status = document.querySelector("#catalogue-status");
  if (!search || !filter || !status) return;

  const update = () => {
    const query = search.value.trim().toLocaleLowerCase("de");
    const kind = filter.value;
    let visible = 0;
    for (const card of cards) {
      const matchesText = !query || (card.dataset.search || "").includes(query);
      const matchesKind = kind === "all" || card.dataset.kind === kind;
      card.hidden = !(matchesText && matchesKind);
      if (!card.hidden) visible += 1;
    }
    status.textContent = `${visible} ${visible === 1 ? "Eintrag" : "Einträge"} sichtbar; nach Erstellungsdatum absteigend sortiert.`;
  };

  search.addEventListener("input", update);
  filter.addEventListener("change", update);
})();

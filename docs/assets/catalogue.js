(() => {
  const search = document.querySelector("#catalogue-search");
  const filter = document.querySelector("#catalogue-filter");
  const language = document.querySelector("#catalogue-language");
  const script = document.querySelector("#catalogue-script");
  const cards = [...document.querySelectorAll(".catalogue-card")];
  const status = document.querySelector("#catalogue-status");
  if (!search || !filter || !language || !script || !status) return;

  const addOptions = (select, values) => {
    [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, "de")).forEach(value => {
      const option = document.createElement("option"); option.value = value; option.textContent = value;
      select.appendChild(option);
    });
  };
  addOptions(language, cards.map(card => card.dataset.language));
  addOptions(script, cards.map(card => card.dataset.script));

  const update = () => {
    const query = search.value.trim().toLocaleLowerCase("de");
    const kind = filter.value;
    let visible = 0;
    for (const card of cards) {
      const matchesText = !query || (card.dataset.search || "").includes(query);
      const matchesKind = kind === "all" || card.dataset.kind === kind;
      const matchesLanguage = language.value === "all" || card.dataset.language === language.value;
      const matchesScript = script.value === "all" || card.dataset.script === script.value;
      card.hidden = !(matchesText && matchesKind && matchesLanguage && matchesScript);
      if (!card.hidden) visible += 1;
    }
    status.textContent = `${visible} ${visible === 1 ? "Eintrag" : "Einträge"} sichtbar; nach Erstellungsdatum absteigend sortiert.`;
  };

  search.addEventListener("input", update);
  filter.addEventListener("change", update);
  language.addEventListener("change", update);
  script.addEventListener("change", update);
})();

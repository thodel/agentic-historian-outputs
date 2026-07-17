const CATALOGUE_DEFAULTS = {
  q: "", kind: "all", language: "all", script: "all", engine: "all",
  readiness: "all", failure: "all", source: "all", sort: "created-desc",
};

function catalogueStateFromParams(params) {
  const state = { ...CATALOGUE_DEFAULTS };
  for (const key of Object.keys(state)) state[key] = params.get(key) || state[key];
  return state;
}

function catalogueMatches(data, state) {
  const number = key => Number(data[key] || 0);
  const engines = (data.recognitionEngines || "").split(",").filter(Boolean);
  const matchesReadiness = state.readiness === "all" ||
    (state.readiness === "comparison" && data.comparisonReady === "true") ||
    (state.readiness === "candidates" && number("recognitionTotal") > 0) ||
    (state.readiness === "legacy" && data.recognitionProvenance === "legacy");
  const hasIssues = number("recognitionFailed") + number("recognitionEmpty") +
    number("recognitionDegenerate") > 0;
  const matchesFailure = state.failure === "all" ||
    (state.failure === "issues" && hasIssues) ||
    (state.failure === "clean" && data.recognitionProvenance !== "legacy" && !hasIssues);
  const matchesSource = state.source === "all" ||
    (state.source === "available" && data.sourceAvailable === "true") ||
    (state.source === "missing" && data.sourceAvailable !== "true") ||
    data.sourceType === state.source;
  return (!state.q || (data.search || "").includes(state.q.toLocaleLowerCase("de"))) &&
    (state.kind === "all" || data.kind === state.kind) &&
    (state.language === "all" || data.language === state.language) &&
    (state.script === "all" || data.script === state.script) &&
    (state.engine === "all" || engines.includes(state.engine)) &&
    matchesReadiness && matchesFailure && matchesSource;
}

function catalogueParams(state) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(state)) {
    if (value && value !== CATALOGUE_DEFAULTS[key]) params.set(key, value);
  }
  return params;
}

function catalogueCompare(left, right, sort) {
  const [field, direction] = sort.split("-");
  const idCompare = (left.documentId || "").localeCompare(right.documentId || "", "de", { numeric: true });
  if (field === "title") return direction === "desc" ? -idCompare : idCompare;
  const key = field === "created" ? "created" :
    field === "pages" ? "recognitionPages" : "recognitionTotal";
  const parse = (data, value) => {
    if (field === "failures") {
      const parts = [data.recognitionFailed, data.recognitionEmpty, data.recognitionDegenerate];
      if (parts.every(part => part === undefined || part === null || part === "")) return null;
      return parts.reduce((sum, part) => sum + Number(part || 0), 0);
    }
    if (value === undefined || value === null || value === "") return null;
    const number = field === "created" ? Date.parse(value) : Number(value);
    return Number.isFinite(number) ? number : null;
  };
  const a = parse(left, left[key]); const b = parse(right, right[key]);
  if (a === null && b !== null) return 1;
  if (a !== null && b === null) return -1;
  if (a !== b) return (a - b) * (direction === "desc" ? -1 : 1);
  return idCompare;
}

function initCatalogue() {
  const ids = ["search", "filter", "language", "script", "engine", "readiness", "failure", "source", "sort"];
  const controls = Object.fromEntries(ids.map(id => [id, document.querySelector(`#catalogue-${id}`)]));
  const clear = document.querySelector("#catalogue-clear");
  const cards = [...document.querySelectorAll(".catalogue-card")];
  const status = document.querySelector("#catalogue-status");
  const active = document.querySelector("#catalogue-active-filters");
  const list = document.querySelector("#catalogue-list");
  if (Object.values(controls).some(control => !control) || !clear || !status || !active || !list) return;
  list.dataset.enhanced = "true";

  const addOptions = (select, values) => {
    [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, "de")).forEach(value => {
      const option = document.createElement("option"); option.value = value; option.textContent = value;
      select.appendChild(option);
    });
  };
  addOptions(controls.language, cards.map(card => card.dataset.language));
  addOptions(controls.script, cards.map(card => card.dataset.script));
  addOptions(controls.engine, cards.flatMap(card => (card.dataset.recognitionEngines || "").split(",")));

  const readState = () => ({
    q: controls.search.value.trim(), kind: controls.filter.value,
    language: controls.language.value, script: controls.script.value,
    engine: controls.engine.value, readiness: controls.readiness.value,
    failure: controls.failure.value, source: controls.source.value, sort: controls.sort.value,
  });
  const writeState = state => {
    controls.search.value = state.q;
    controls.filter.value = state.kind;
    for (const key of ["language", "script", "engine", "readiness", "failure", "source", "sort"])
      controls[key].value = state[key];
  };
  const update = ({ push = true } = {}) => {
    const state = readState();
    cards.sort((left, right) => catalogueCompare(left.dataset, right.dataset, state.sort));
    for (const card of cards) list.appendChild(card);
    let visible = 0;
    for (const card of cards) {
      card.hidden = !catalogueMatches(card.dataset, state);
      if (!card.hidden) visible += 1;
    }
    const filters = Object.entries(state).filter(([key, value]) => key !== "sort" && value && value !== CATALOGUE_DEFAULTS[key]);
    const sortLabel = controls.sort.options[controls.sort.selectedIndex].textContent;
    active.textContent = filters.length ? `Aktive Filter: ${filters.map(([, value]) => value).join(", ")}.` : "Keine Filter aktiv.";
    status.textContent = visible
      ? `${visible} ${visible === 1 ? "Eintrag" : "Einträge"} sichtbar; Sortierung: ${sortLabel}.`
      : `Keine Einträge entsprechen den aktiven Filtern (${filters.map(([, value]) => value).join(", ") || "keine"}).`;
    if (push) {
      const url = new URL(window.location.href); url.search = catalogueParams(state).toString();
      history.pushState(state, "", url);
    }
  };

  writeState(catalogueStateFromParams(new URL(window.location.href).searchParams));
  update({ push: false });
  controls.search.addEventListener("input", update);
  for (const control of Object.values(controls).filter(control => control !== controls.search))
    control.addEventListener("change", update);
  clear.addEventListener("click", () => { writeState({ ...CATALOGUE_DEFAULTS }); update(); controls.search.focus(); });
  addEventListener("popstate", () => {
    writeState(catalogueStateFromParams(new URL(window.location.href).searchParams));
    update({ push: false });
  });
}

if (typeof document !== "undefined") initCatalogue();
if (typeof module !== "undefined") module.exports = {
  CATALOGUE_DEFAULTS, catalogueCompare, catalogueMatches, catalogueParams, catalogueStateFromParams,
};

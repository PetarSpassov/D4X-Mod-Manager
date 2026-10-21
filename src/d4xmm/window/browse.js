// The Browse tab: Nexus's catalog for the game; loaded after page.js, whose call, meta, stats,
// day and FOLD_MS it uses. Download opens the Files tab: the keyless API gives no download links.
let catalog = null;  // asked for when the tab is first opened, then on Reload
const opened = new Set();  // nexus ids whose card is open; kept across re-renders
const tagFilter = new Map();  // tag name: "in" (the mod must have it) or "out" (must not)
const BROWSE_ERROR = {offline: "You are offline, so Nexus's mods can't be listed.",
                      refused: "Nexus answered with an error. Try reloading in a while."};
const NEXT_STATE = {undefined: "in", in: "out", out: undefined};

function cardDetail(m) {
  const box = document.createElement("div");
  box.className = "detail";
  box.innerHTML = '<div class="about"><p class="stats"></p><div class="tags"></div>' +
    '<p class="description"></p></div>';
  const dates = [];
  if (m.created) dates.push("first uploaded " + day(m.created));
  if (m.updated) dates.push("updated " + day(m.updated));
  box.querySelector(".stats").textContent = dates.join(" · ");
  for (const tag of m.tags) {
    const chip = document.createElement("button");
    chip.className = "chip " + (tagFilter.get(tag) || "");
    chip.textContent = tag;
    chip.title = "Show only mods with this tag";
    chip.onclick = () => { tagFilter.set(tag, "in"); renderCatalog(); };
    box.querySelector(".tags").appendChild(chip);
  }
  box.querySelector(".description").textContent =
    m.description || m.summary || "Nexus has no description for this mod.";
  return box;
}

function toggleCard(m, li) {
  const open = !opened.delete(m.nexus_id);
  const old = li.querySelector(".detail");
  if (old) old.classList.add("closing");
  if (open) {
    opened.add(m.nexus_id);
    if (old) old.remove();  // still folding from a quick second click
    li.appendChild(cardDetail(m));
  } else {
    setTimeout(() => old.remove(), FOLD_MS);  // a timer, as in page.js's toggle
  }
  li.classList.toggle("open", open);
}

function card(m) {
  const li = document.createElement("li");
  li.innerHTML = '<div class="top"><span class="thumb"><img alt=""></span><div class="about">' +
    '<div class="title"><span class="name"></span> <span class="meta"></span></div>' +
    '<p class="stats"></p><p class="summary"></p></div><button>Download</button></div>';
  const img = li.querySelector("img");
  if (m.thumbnail || m.picture) img.src = m.thumbnail || m.picture;
  else img.remove();
  if (mods.some(x => x.nexus_id === m.nexus_id)) {  // page.js's library list, always current
    li.querySelector(".thumb").insertAdjacentHTML("beforeend",
      '<span class="have" title="This mod is in your library">✓ In library</span>');
  }
  li.querySelector(".name").textContent = m.name;
  li.querySelector(".meta").textContent = meta(m);
  li.querySelector(".title").title = m.name + " " + meta(m);
  li.querySelector(".stats").textContent = stats(m);
  li.querySelector(".summary").textContent = m.summary || "";
  const button = li.querySelector("button");
  button.title = "Open its Files page on Nexus";
  button.onclick = e => { e.stopPropagation(); call("open_nexus_files", m.nexus_id); };
  li.querySelector(".top").onclick = () => toggleCard(m, li);
  if (opened.has(m.nexus_id)) {
    li.classList.add("open");
    li.appendChild(cardDetail(m)).classList.add("still");
  }
  return li;
}

function shows(m, query) {
  if (query && !m.name.toLowerCase().includes(query)) return false;
  for (const [tag, want] of tagFilter) {
    if (m.tags.includes(tag) !== (want === "in")) return false;
  }
  return true;
}

function renderTagMenu() {
  const counts = new Map();
  catalog.mods.forEach(m => m.tags.forEach(t => counts.set(t, (counts.get(t) || 0) + 1)));
  const list = $("tag-list");
  list.innerHTML = counts.size ? "" : '<li class="hint">Nexus lists no tags for these mods.</li>';
  for (const [tag, n] of [...counts].sort((a, b) => a[0].localeCompare(b[0]))) {
    const li = item("", tagFilter.get(tag) || "");
    li.innerHTML = '<span class="mark"></span><span class="tag-name"></span>' +
      '<span class="n"></span>';
    li.querySelector(".tag-name").textContent = tag;
    li.querySelector(".n").textContent = n;
    li.onclick = () => {
      const next = NEXT_STATE[tagFilter.get(tag)];
      if (next) tagFilter.set(tag, next);
      else tagFilter.delete(tag);
      renderCatalog();
    };
    list.appendChild(li);
  }
  $("tag-filter").classList.toggle("on", tagFilter.size > 0);
  $("tag-count").textContent = tagFilter.size || "";
}

function renderCatalog() {
  const list = $("catalog");
  const query = $("browse-search").value.trim().toLowerCase();
  const shown = catalog.mods.filter(m => shows(m, query));
  list.innerHTML = "";
  if (catalog.error) {
    list.innerHTML = '<li class="empty"></li>';
    list.firstChild.textContent = BROWSE_ERROR[catalog.error];
  } else if (!shown.length) {
    list.innerHTML = '<li class="empty">No mods on Nexus match the search and tags.</li>';
  }
  shown.forEach(m => list.appendChild(card(m)));
  const total = catalog.mods.length;
  $("browse-count").textContent = catalog.error ? "" :
    shown.length === total ? `${total} mods on Nexus` : `${shown.length} of ${total} mods`;
  renderTagMenu();
}

async function loadCatalog() {
  $("catalog").innerHTML = '<li class="empty">Asking Nexus…</li>';
  const found = await call("browse");
  catalog = found || {mods: [], error: "refused"};  // call() put the reason in the status line
  renderCatalog();
}

document.querySelector('.tab[data-tab="browse"]').addEventListener("click", () => {
  if (catalog) renderCatalog();  // an import since may have put a mod in the library
  else loadCatalog();
});
$("browse-reload").onclick = loadCatalog;
$("browse-search").oninput = () => { if (catalog) renderCatalog(); };
$("tag-filter").onclick = () => { $("tag-menu").hidden = !$("tag-menu").hidden; };
$("tag-clear").onclick = () => { tagFilter.clear(); renderCatalog(); };
document.addEventListener("click", e => {
  // the path, not closest(): a click in the menu re-renders it, so its target is already gone
  if (!e.composedPath().includes($("tag-picker"))) $("tag-menu").hidden = true;
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape") $("tag-menu").hidden = true;
});

// The Browse tab: Nexus's catalog for the game; loaded after page.js, whose call, meta, stats uses.
// Download opens the mod's Files tab in the browser: the keyless API gives no download links.
let catalog = null;  // asked for when the tab is first opened, then on Reload
const BROWSE_ERROR = {offline: "You are offline, so Nexus's mods can't be listed.",
                      refused: "Nexus answered with an error. Try Reload in a while."};

function card(m) {
  const li = document.createElement("li");
  li.innerHTML = '<img alt=""><div class="about"><div class="title"><span class="name"></span> ' +
    '<span class="meta"></span></div><p class="stats"></p><p class="summary"></p></div>';
  const img = li.querySelector("img");
  if (m.thumbnail || m.picture) img.src = m.thumbnail || m.picture;
  else img.remove();
  li.querySelector(".name").textContent = m.name;
  li.querySelector(".meta").textContent = meta(m);
  li.querySelector(".title").title = m.name + " " + meta(m);
  li.querySelector(".stats").textContent = stats(m);
  li.querySelector(".summary").textContent = m.summary || "Nexus has no summary for this mod.";
  const button = document.createElement("button");
  button.textContent = "Download";
  button.title = "Open its Files page on Nexus";
  button.onclick = () => call("open_nexus_files", m.nexus_id);
  if (mods.some(x => x.nexus_id === m.nexus_id)) {  // page.js's library list, always current
    li.insertAdjacentHTML("beforeend", '<span class="note have">in library</span>');
    button.textContent = "Files";
  }
  li.appendChild(button);
  return li;
}

function renderCatalog() {
  const list = $("catalog");
  const query = $("browse-search").value.trim().toLowerCase();
  list.innerHTML = "";
  if (catalog.error) {
    list.innerHTML = '<li class="empty"></li>';
    list.firstChild.textContent = BROWSE_ERROR[catalog.error];
  } else if (!catalog.mods.length) {
    list.innerHTML = '<li class="empty">Nexus lists no mods for Dune: Spice Wars.</li>';
  }
  const shown = catalog.mods.filter(m => !query || m.name.toLowerCase().includes(query));
  shown.forEach(m => list.appendChild(card(m)));
  $("browse-count").textContent = catalog.error ? "" : `${catalog.mods.length} mods on Nexus`;
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

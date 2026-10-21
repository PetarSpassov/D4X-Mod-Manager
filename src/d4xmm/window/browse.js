// The Browse tab, Nexus's catalog, and the Nexus lines in Settings (key, link handler); loaded
// after page.js, whose call, run, item, meta, stats, day and FOLD_MS it uses.
let catalog = null;  // asked for when the tab is first opened, then on Reload
const opened = new Set();  // nexus ids whose card is open; kept across re-renders
const tagFilter = new Map();  // tag name: "in" (the mod must have it) or "out" (must not)
const BROWSE_ERROR = {offline: "You are offline, so Nexus's mods can't be listed.",
                      refused: "Nexus answered with an error. Try reloading in a while."};
const NEXT_STATE = {undefined: "in", in: "out", out: undefined};
let account = {key: "checking"};  // Api.state()'s: whose key it is, and Premium
const downloading = new Set();  // nexus ids being downloaded, so a re-render keeps their button
const KEY_STATE = {
  none: "Paste your personal API key to see your account here.",
  checking: "Checking the key with Nexus…",
  unchecked: "Nexus couldn't be reached to check this key; it is checked again next start.",
  invalid: "Nexus doesn't accept this key. Get a new one and paste it here.",
};
const by = key => (a, b) => {  // highest first; updated is an ISO time, so it compares as text
  const x = a[key] ?? "", y = b[key] ?? "";
  return x < y ? 1 : x > y ? -1 : 0;
};
const SORTS = {"Most downloaded": by("downloads"), "Most endorsed": by("endorsements"),
               "Last updated": by("updated"),
               "Name, A to Z": (a, b) => a.name.localeCompare(b.name)};
let sortName = "Most downloaded";

function cardDetail(m) {
  const box = document.createElement("div");
  box.className = "detail";
  box.innerHTML = '<div class="about"><p class="stats"></p><div class="tags"></div>' +
    '<div class="description"></div></div>';  // a div: a <p> can't hold the lists
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
  const text = box.querySelector(".description");
  // catalog.py's bbcode.to_html escaped every piece of the author's text first
  if (m.description) text.innerHTML = m.description;
  else text.textContent = m.summary || "Nexus has no description for this mod.";
  text.onclick = e => {
    const link = e.target.closest("a[href]");
    if (!link) return;
    e.preventDefault();  // in the user's browser, not in place of the app
    call("open_link", link.getAttribute("href"));
  };
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
  button.title = account.premium ? "Download its newest main file and import it"
                                 : "Open its Files page on Nexus";
  button.onclick = e => {
    e.stopPropagation();
    if (account.premium) downloadInApp(m, button);
    else call("open_nexus_files", m.nexus_id);
  };
  if (downloading.has(m.nexus_id)) {
    button.disabled = true;
    button.textContent = "Downloading…";
  }
  li.querySelector(".top").onclick = () => toggleCard(m, li);
  if (opened.has(m.nexus_id)) {
    li.classList.add("open");
    li.appendChild(cardDetail(m)).classList.add("still");
  }
  return li;
}

function renderAccount(a) {
  account = a;
  const line = $("key-state");
  line.className = a.key === "invalid" ? "error" : "hint";
  line.textContent = a.key !== "ok" ? KEY_STATE[a.key] :
    `Signed in as ${a.name} · ` + (a.premium ? "Premium: Download gets mods in the app."
                                            : "Free: Download opens the mod's Files page.");
}

function renderLinks(l) {
  $("links-state").textContent = l.ours ? "Its downloads come to this app." :
    (l.other ? `Its downloads go to ${l.other}.` : "No program takes its downloads.") +
    " Taking them over needs your API key, Free or Premium.";
  $("links-toggle").textContent = l.ours ? "Give back" : "Use this app";
  $("links-toggle").title = l.ours ? "Hand the links back to the program that had them"
                                   : "Windows sends Nexus's mod manager links here";
  $("links-toggle").onclick = () => run(l.ours ? "release_links" : "take_links");
}

// not through call(): a download takes a while, and the rest of the window stays usable
async function downloadInApp(m, button) {
  if (downloading.has(m.nexus_id)) return;  // page.js's busy() may have re-enabled the button
  downloading.add(m.nexus_id);
  button.disabled = true;
  button.textContent = "Downloading…";
  let failed = "";
  try {
    render(await window.pywebview.api.download_mod(m.nexus_id));
  } catch (e) {
    failed = String(e.message || e);
  }
  downloading.delete(m.nexus_id);
  renderCatalog();  // the card shows "In library", the button "Download" again
  if (failed) {  // in the Browse toolbar: the status line is on the Installed tab
    $("browse-count").textContent = m.name + ": " + failed;
    $("browse-count").className = "error";
  }
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

function renderSortMenu() {
  const list = $("sort-list");
  list.innerHTML = "";
  for (const name of Object.keys(SORTS)) {
    const li = item(name, name === sortName ? "current" : "");
    li.onclick = () => {
      sortName = name;
      $("sort-list").hidden = true;
      renderCatalog();
    };
    list.appendChild(li);
  }
  $("sort").title = "Sort: " + sortName;
}

function renderCatalog() {
  const list = $("catalog");
  const query = $("browse-search").value.trim().toLowerCase();
  const shown = catalog.mods.filter(m => shows(m, query)).sort(SORTS[sortName]);
  list.innerHTML = "";
  if (catalog.error) {
    list.innerHTML = '<li class="empty"></li>';
    list.firstChild.textContent = BROWSE_ERROR[catalog.error];
  } else if (!shown.length) {
    list.innerHTML = '<li class="empty">No mods on Nexus match the search and tags.</li>';
  }
  shown.forEach(m => list.appendChild(card(m)));
  const total = catalog.mods.length;
  $("browse-count").className = "";
  $("browse-count").textContent = catalog.error ? "" :
    shown.length === total ? `${total} mods on Nexus` : `${shown.length} of ${total} mods`;
  renderTagMenu();
  renderSortMenu();
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
$("get-key").onclick = () => call("open_key_page");
$("browse-search").oninput = () => { if (catalog) renderCatalog(); };
$("tag-clear").onclick = () => { tagFilter.clear(); renderCatalog(); };
const MENUS = [["tag-picker", "tag-filter", "tag-menu"], ["sort-picker", "sort", "sort-list"]];
for (const [, button, menu] of MENUS) {
  $(button).onclick = () => {
    const open = $(menu).hidden;
    MENUS.forEach(([, , other]) => { $(other).hidden = true; });
    $(menu).hidden = !open;
  };
}
document.addEventListener("click", e => {
  // the path, not closest(): a click in a menu re-renders it, so its target is already gone
  for (const [picker, , menu] of MENUS) {
    if (!e.composedPath().includes($(picker))) $(menu).hidden = true;
  }
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape") MENUS.forEach(([, , menu]) => { $(menu).hidden = true; });
});

// The window's page: renders Api.state() and sends every change back through window.pywebview.api.
let mods = [];
let dragFrom = null;
const expanded = new Set();  // folders whose detail is open; kept across re-renders
const NO_VERSION = {offline: "You are offline", not_found: "This file is not on Nexus",
                    refused: "Nexus answered with an error"};
const STATUS = {none: "Not installed", current: "Installed, up to date",
                changed: "Changed since last install", unknown: "Installed"};
const $ = id => document.getElementById(id);

function setStatus(text, warn) {
  $("status").textContent = text;
  $("status").className = warn ? "warn" : "";
}

function busy(on) {
  document.querySelectorAll("button, input").forEach(b => { b.disabled = on; });
}

async function call(name, ...args) {
  busy(true);
  try {
    return await window.pywebview.api[name](...args);
  } catch (e) {
    setStatus(String(e.message || e), true);
    return null;
  } finally {
    busy(false);
  }
}

async function run(name, ...args) {
  const state = await call(name, ...args);
  if (state) render(state);
  return state;
}

function note(m) {
  if (!m.version) {
    return {cls: "unknown", text: m.nexus === "offline" ? "offline" : "not on Nexus",
            title: "Could not determine version. " + (NO_VERSION[m.nexus] || "")};
  }
  if (m.latest && m.latest !== m.version) {
    return {cls: "update", text: "update: " + m.latest, title: "A newer main file is on Nexus"};
  }
  return null;
}

function closeMenus(except) {
  document.querySelectorAll(".menu[open]").forEach(o => { if (o !== except) o.open = false; });
}

function menu(m, li) {
  const box = document.createElement("details");
  box.className = "menu";
  box.innerHTML = '<summary title="More">⋯</summary><div class="items">' +
    '<button data-act="folder">Open folder</button>' +
    '<button data-act="nexus">Open on Nexus</button>' +
    '<button data-act="delete" class="danger">Delete from library</button></div>';
  box.querySelector('[data-act="nexus"]').disabled = !m.nexus_id;
  box.querySelector('[data-act="folder"]').onclick = () => call("open_folder", m.folder);
  box.querySelector('[data-act="nexus"]').onclick = () => call("open_nexus", m.folder);
  const del = box.querySelector('[data-act="delete"]');
  del.onclick = () => {
    if (del.dataset.armed) { run("delete", m.folder); return; }
    del.dataset.armed = "1";
    del.textContent = "Click again to delete";
  };
  box.addEventListener("toggle", () => { if (box.open) closeMenus(box); });
  li.appendChild(box);
}

function meta(m) {
  const parts = [];
  if (m.version) parts.push(/^v/i.test(m.version) ? m.version : "v" + m.version);
  if (m.creator) parts.push("by " + m.creator);
  return parts.join(" ");
}

function detail(m) {
  const box = document.createElement("div");
  box.className = "detail";
  if (m.picture) {
    const img = document.createElement("img");
    img.src = m.picture;
    img.alt = "";
    box.appendChild(img);
  }
  const text = document.createElement("p");
  text.textContent = m.summary || "Nexus has no summary for this mod.";
  box.appendChild(text);
  return box;
}

function row(m, i) {
  const li = document.createElement("li");
  li.className = (m.enabled ? "" : "off") + (expanded.has(m.folder) ? " open" : "");
  li.draggable = true;
  li.dataset.index = i;
  li.innerHTML = '<div class="line"><span class="handle" title="Drag to reorder">⠿</span>' +
    '<input type="checkbox"><span class="title"><span class="name"></span> ' +
    '<span class="meta"></span></span></div>';
  const line = li.querySelector(".line");
  li.querySelector("input").checked = m.enabled;
  li.querySelector("input").onchange = e => { m.enabled = e.target.checked; save(); };
  li.querySelector(".name").textContent = m.name;
  li.querySelector(".meta").textContent = meta(m);
  li.querySelector(".title").title = m.name + " " + meta(m);
  const n = note(m);
  if (n) {
    const tag = document.createElement("span");
    tag.className = "note " + n.cls;
    tag.textContent = n.text;
    tag.title = n.title;
    line.appendChild(tag);
  }
  menu(m, line);
  line.addEventListener("click", e => {
    if (e.target.closest("input, .menu, .handle")) return;
    if (!expanded.delete(m.folder)) expanded.add(m.folder);
    li.classList.toggle("open");
    if (li.classList.contains("open") && !li.querySelector(".detail")) li.appendChild(detail(m));
  });
  if (expanded.has(m.folder)) li.appendChild(detail(m));
  dragEvents(li);
  return li;
}

function dragEvents(li) {
  li.addEventListener("dragstart", e => {
    dragFrom = Number(li.dataset.index);
    li.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  });
  li.addEventListener("dragend", () => { dragFrom = null; li.classList.remove("dragging"); });
  li.addEventListener("dragover", e => {
    if (dragFrom === null) return;
    e.preventDefault();
    const after = e.offsetY > li.offsetHeight / 2;
    li.classList.toggle("drop-after", after);
    li.classList.toggle("drop-before", !after);
  });
  li.addEventListener("dragleave", () => li.classList.remove("drop-after", "drop-before"));
  li.addEventListener("drop", e => {
    if (dragFrom === null) return;
    e.preventDefault();
    let to = Number(li.dataset.index) + (li.classList.contains("drop-after") ? 1 : 0);
    li.classList.remove("drop-after", "drop-before");
    const [moved] = mods.splice(dragFrom, 1);
    if (to > dragFrom) to -= 1;
    mods.splice(to, 0, moved);
    save();
  });
}

function renderList() {
  const list = $("mods");
  const query = $("search").value.trim().toLowerCase();
  list.innerHTML = "";
  if (!mods.length) {
    list.innerHTML = '<li class="empty">No mods yet. Import or drop a mod\'s zip, 7z or rar.</li>';
  }
  mods.forEach((m, i) => {
    if (!query || m.name.toLowerCase().includes(query)) list.appendChild(row(m, i));
  });
}

function renderLast(install) {
  const last = $("last");
  last.hidden = !install.clashes.length;
  const lines = install.clashes.map(c =>
    `${c.winner} overrides ${c.over.join(", ")} on ${c.items.length} ` +
    (c.items.length === 1 ? "item" : "items"));
  last.querySelector("summary").textContent = "Last install: " + lines.join("; ");
  const ul = last.querySelector("ul");
  ul.innerHTML = "";
  for (const c of install.clashes) {
    for (const item of c.items) {
      const li = document.createElement("li");
      li.textContent = `${item}: ${c.winner} over ${c.over.join(", ")}`;
      ul.appendChild(li);
    }
  }
}

function renderSettings(s) {
  for (const key of ["game_dir", "downloads"]) {
    const input = $("set-" + key);
    if (document.activeElement !== input) input.value = s[key] || "";
  }
  $("game-error").hidden = s.game_ok;
  $("set-game_dir").classList.toggle("bad", !s.game_ok);
}

function render(state) {
  mods = state.mods;
  renderSettings(state.settings);
  const pill = $("install-state");
  pill.textContent = STATUS[state.install.status];
  pill.className = "pill " + state.install.status;
  const ticked = mods.filter(m => m.enabled).length;
  $("install").textContent = `Install (${ticked} ${ticked === 1 ? "mod" : "mods"})`;
  renderList();
  renderLast(state.install);
}

function save() {
  run("save_order", mods.map(m => ({folder: m.folder, enabled: m.enabled})));
}

function describe(report) {
  const lines = ["Installed."];
  const merged = report.merge;
  if (merged && merged.traits_over) {
    lines.push(`Warning: ${merged.traits} traits. The game crashes past 2,048; ` +
               "this is a limit of the game, not the manager.");
  }
  for (const [mod, sheets] of Object.entries((merged && merged.cdb) || {})) {
    for (const [sheet, r] of Object.entries(sheets)) {
      if (r.dropped.length) {
        lines.push(`${mod}: kept ${r.dropped.length} ${sheet} rows it removes.`);
      }
      if (r.no_id) lines.push(`${mod}: skipped ${r.no_id} ${sheet} rows with no id.`);
    }
  }
  if (report.hlboot_modded.length) {
    lines.push("Note: " + report.hlboot_modded.join(", ") + " already carry a mod's mark, " +
               "so the backup is not the stock game.");
  }
  if (report.skipped.length) lines.push("Left alone (changed since): " + report.skipped.join(", "));
  return {text: lines.join("\n"), warn: lines.length > 1};
}

async function importDropped(paths) {
  if (await run("import_paths", paths)) setStatus("");
}

function showTab(name) {
  document.querySelectorAll(".tab").forEach(t => {
    t.classList.toggle("active", t.dataset.tab === name);
  });
  document.querySelectorAll(".page").forEach(p => { p.hidden = p.id !== "tab-" + name; });
}

document.querySelectorAll(".tab").forEach(t => { t.onclick = () => showTab(t.dataset.tab); });
document.querySelectorAll("[data-key]").forEach(input => {
  input.onchange = () => run("set_folder", input.dataset.key, input.value);
});
document.querySelectorAll("[data-choose]").forEach(b => {
  b.onclick = () => run("choose_folder", b.dataset.choose);
});

$("import").onclick = async () => { if (await run("import_mods")) setStatus(""); };
$("search").oninput = renderList;

$("install").onclick = async () => {
  setStatus("Merging and installing… this can take a minute.");
  const report = await call("install");
  if (report) {
    const d = describe(report);
    setStatus(d.text, d.warn);
    await run("state");
  }
};

$("restore").onclick = async () => {
  const skipped = await call("restore");
  if (skipped) {
    setStatus(skipped.length ? "Removed. Left alone (changed since): " + skipped.join(", ")
                             : "Removed. The game is back to its base files.", skipped.length > 0);
    await run("state");
  }
};

document.addEventListener("dragover", e => e.preventDefault());  // lets files be dropped anywhere
document.addEventListener("click", e => { if (!e.target.closest(".menu")) closeMenus(null); });

window.addEventListener("pywebviewready", async () => {
  await run("state");
  // not through call(): the list stays usable while Nexus answers
  window.pywebview.api.refresh().then(render, e => setStatus(String(e.message || e), true));
});

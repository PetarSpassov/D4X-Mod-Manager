// Mods arriving: Downloads-folder offers in the bar under the tabs, and Nexus's mod manager
// links. Loaded after page.js, whose run, render, setStatus and showTab it uses.
const WATCH_SECONDS = 1;  // a folder listing: cheap; Nexus is asked once per new archive

function renderOffers(offers) {
  const bar = $("offers");
  bar.innerHTML = "";
  for (const o of offers) {
    const row = document.createElement("div");
    row.className = "offer";
    row.innerHTML = '<span class="offer-text">Downloaded: <b></b> <span class="meta"></span>' +
      '</span><button class="primary">Import</button>' +
      '<button class="icon" title="Don\'t offer this again">' +
      '<svg viewBox="0 0 16 16"><path d="M4 4l8 8M12 4l-8 8"/></svg></button>';
    row.querySelector("b").textContent = o.name;
    row.querySelector(".meta").textContent = o.version ? "v" + o.version.replace(/^v/i, "") : "";
    row.querySelector(".primary").onclick = async () => {
      if (await run("import_download", o.file)) setStatus("Imported " + o.name + ".", "ok");
      watch();
    };
    row.querySelector(".icon").onclick = async () => {
      await window.pywebview.api.dismiss_download(o.file);
      watch();
    };
    bar.appendChild(row);
  }
  bar.hidden = !offers.length;
}

// not through call(): a look every few seconds mustn't grey the buttons out
async function watch() {
  try {
    renderOffers(await window.pywebview.api.downloads());
  } catch (e) {
    console.warn("Downloads folder not read:", e);  // the next look tries again
  }
}

// the next look starts a second after this one ends: offline, Nexus takes up to 10s to fail,
// and a fixed interval would pile up looks asking about the same archive
async function watchLoop() {
  await watch();
  setTimeout(watchLoop, WATCH_SECONDS * 1000);
}

// a website "Mod Manager Download" link; app.py hands it over, or pending_link() at start
async function nxmLink(url) {
  showTab("installed");  // where the status line is
  setStatus("Downloading from Nexus…");
  try {
    render(await window.pywebview.api.download_link(url));
    setStatus("Downloaded and imported.", "ok");
  } catch (e) {
    setStatus(String(e.message || e), "warn");
  }
}

window.addEventListener("pywebviewready", async () => {
  watchLoop();
  const link = await window.pywebview.api.pending_link();
  if (link) nxmLink(link);
});

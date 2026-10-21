// The Installed toolbar's profile picker; loaded after page.js, whose run, item and armed it uses.
// Our own list, not a <select>: Windows draws a select's open list square, with a white hover.
let profileState = {active: "", names: []};

function renderProfiles(p) {
  profileState = p;
  $("profile").textContent = p.active;
  const list = $("profile-list");
  list.innerHTML = "";
  for (const name of p.names) {
    const li = item(name, name === p.active ? "current" : "");
    li.onclick = () => {
      list.hidden = true;
      if (name !== p.active) run("switch_profile", name);
    };
    list.appendChild(li);
  }
  $("profile-delete").disabled = p.names.length < 2;
}

function profileForm(open) {
  $("profile-form").hidden = !open;
  $("profile-list").hidden = true;
  for (const id of ["profile-picker", "profile-new", "profile-delete"]) $(id).hidden = open;
  if (open) {
    $("profile-name").value = "";
    $("profile-name").focus();
  }
}

async function createProfile() {
  if (await run("new_profile", $("profile-name").value)) profileForm(false);
}

$("profile").onclick = () => { $("profile-list").hidden = !$("profile-list").hidden; };
$("profile-new").onclick = () => profileForm(true);
$("profile-cancel").onclick = () => profileForm(false);
$("profile-create").onclick = createProfile;
$("profile-name").onkeydown = e => {
  if (e.key === "Enter") createProfile();
  if (e.key === "Escape") profileForm(false);
};
armed($("profile-delete"), () => run("delete_profile", profileState.active));
document.addEventListener("click", e => {
  if (!e.target.closest("#profile-picker")) $("profile-list").hidden = true;
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape") $("profile-list").hidden = true;
});

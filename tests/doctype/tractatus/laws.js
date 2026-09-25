() => {
  const errs = [];
  const tree = document.getElementById("outline");
  const items = [...tree.querySelectorAll('[role="treeitem"]')];
  const st = window.tractatus.state();
  const expanded = new Set(st.expanded);
  const up = (li) => li.parentElement.closest('[role="treeitem"]');
  // Law Q: while a query filters, a treeitem below the displayed root is displayed exactly when
  // find() shows it, and a shown parent is open exactly when it has a shown child.
  const find = typeof window.tractatus.find === "function" ? window.tractatus.find() : { query: "", shown: [] };
  const filtering = find.query.trim() !== "";
  const shownSet = new Set(find.shown);

  // Root: the document is the tree's one top-level treeitem. It is always open and shown, never
  // in state().expanded, and the parent of every top-level item.
  const root = document.getElementById("item-root");
  const tops = items.filter((li) => up(li) === null);
  if (tops.length !== 1 || tops[0] !== root) errs.push(`top-level treeitems: ${tops.map((li) => li.id)}`);
  if (root) {
    const zoom = typeof window.tractatus.zoom === "function" ? window.tractatus.zoom() : "root";
    if (root.dataset.id !== zoom) errs.push(`displayed root ${root.dataset.id} is not the zoom ${zoom}`);
    // Law Z: the crumbs list the zoom's ancestors, the document first, outside the tree.
    const crumbs = document.getElementById("crumbs");
    if (crumbs) {
      if (crumbs.hidden !== (zoom === "root")) errs.push(`crumbs hidden=${crumbs.hidden} at zoom ${zoom}`);
      const hrefs = [...crumbs.querySelectorAll("a")].map((a) => a.getAttribute("href"));
      if (zoom !== "root" && hrefs[0] !== "#z=root") errs.push(`first crumb ${hrefs[0]}`);
      if (hrefs.some((h) => !h.startsWith("#z="))) errs.push("crumb without #z=");
      if (tree.contains(crumbs)) errs.push("crumbs inside the tree");
    }
    const box = document.getElementById("find-input");
    if (box && tree.contains(box)) errs.push("find box inside the tree");
    if (root.hidden) errs.push("displayed root is hidden");
    if (expanded.has("root")) errs.push("root is in expanded");
    const group = root.querySelector(':scope > [role="group"]');
    if (group && (group.hidden || root.getAttribute("aria-expanded") !== "true")) errs.push("root is collapsed");
    if (!group && root.hasAttribute("aria-expanded")) errs.push("childless root has aria-expanded");
    if (root.querySelector(":scope > .row > .toggle")) errs.push("root has a toggle");
    if (tree.checkVisibility() && !root.checkVisibility()) errs.push("root is hidden");
  }

  for (const li of items) {
    const id = li.dataset.id;
    const group = li.querySelector(':scope > [role="group"]');
    if (li === root) continue;
    if (filtering) {
      if (li.hidden === shownSet.has(id)) errs.push(`${id}: hidden=${li.hidden}, shown=${shownSet.has(id)}`);
      if (group) {
        const want = [...group.children].some((c) => shownSet.has(c.dataset.id));
        if (li.getAttribute("aria-expanded") !== String(want)) errs.push(`${id}: filter openness`);
      }
    } else if (li.hidden) errs.push(`${id}: hidden without a filter`);
    if (group) {
      if (li.getAttribute("aria-expanded") !== String(!group.hidden)) errs.push(`${id}: aria-expanded disagrees with group`);
      if (!filtering && expanded.has(id) === group.hidden) errs.push(`${id}: state disagrees with DOM expansion`);
    } else {
      if (li.hasAttribute("aria-expanded")) errs.push(`${id}: leaf has aria-expanded`);
      if (expanded.has(id)) errs.push(`${id}: leaf in expanded`);
    }
    let shown = !li.hidden;
    for (let a = up(li); a; a = up(a)) if (a.getAttribute("aria-expanded") !== "true" || a.hidden) shown = false;
    if (li.checkVisibility() !== shown) errs.push(`${id}: visible=${li.checkVisibility()} expected ${shown}`);
  }
  const stops = items.filter((li) => li.getAttribute("tabindex") === "0");
  const want = items.length > 0 ? 1 : 0;
  if (stops.length !== want) errs.push(`${stops.length} treeitems have tabindex=0`);
  if ((stops[0]?.dataset.id ?? null) !== st.activeId) errs.push(`active ${st.activeId} is not the Tab stop`);
  if (stops[0] && !stops[0].checkVisibility()) errs.push(`active ${st.activeId} is hidden`);
  const tabbable = [...tree.querySelectorAll("*")].filter((e) => e.tabIndex >= 0 && e.checkVisibility());
  if (tabbable.length !== want) errs.push(`${tabbable.length} Tab stops inside the tree`);
  const ae = document.activeElement;
  if (tree.contains(ae) && ae !== stops[0]) errs.push("focus is inside the tree but not on the active item");

  // Mode: the tree's data-mode is the state's mode. Idle selects, highlights and rings nothing.
  // Selected mode rings the active row whenever focus is in the tree.
  const sel = window.tractatus.selection();
  if (!["selected", "idle"].includes(sel.mode)) errs.push(`mode ${sel.mode}`);
  if (tree.dataset.mode !== sel.mode) errs.push(`data-mode ${tree.dataset.mode} is not ${sel.mode}`);
  if (sel.activeId !== st.activeId) errs.push("selection and state disagree on the active item");
  if (tree.getAttribute("aria-multiselectable") !== "true") errs.push("tree is not aria-multiselectable");

  // Selection: a run of sibling treeitems from the anchor to the focus end (the active item),
  // each with its whole subtree; anchor === active is the active item alone; idle is empty.
  const byId = (id) => items.find((li) => li.dataset.id === id);
  const chosen = new Set();
  if (sel.mode === "idle" || st.activeId === null) {
    if (sel.anchorId !== st.activeId) errs.push(`idle keeps anchor ${sel.anchorId}`);
  } else if (sel.anchorId === st.activeId) {
    chosen.add(st.activeId);
  } else {
    const a = byId(sel.anchorId);
    const f = byId(st.activeId);
    if (!a || a.parentElement !== f.parentElement) errs.push(`anchor ${sel.anchorId} is not a sibling of ${st.activeId}`);
    else {
      const sibs = [...f.parentElement.children];
      const [i, j] = [sibs.indexOf(a), sibs.indexOf(f)].sort((x, y) => x - y);
      for (const li of sibs.slice(i, j + 1)) {
        chosen.add(li.dataset.id);
        for (const d of li.querySelectorAll('[role="treeitem"]')) chosen.add(d.dataset.id);
      }
    }
  }
  const reported = new Set(sel.selected);
  if (reported.size !== chosen.size || [...chosen].some((id) => !reported.has(id))) errs.push("selection().selected disagrees with the range");
  const transparent = (c) => c === "rgba(0, 0, 0, 0)" || c === "transparent";
  const ringed = ae === stops[0] && sel.mode === "selected" ? stops[0] : null;
  for (const li of items) {
    const id = li.dataset.id;
    const on = chosen.has(id);
    const aria = li.getAttribute("aria-selected");
    if (aria !== "true" && aria !== "false") errs.push(`${id}: aria-selected is ${aria}`);
    else if ((aria === "true") !== on) errs.push(`${id}: aria-selected=${aria}, selected=${on}`);
    if (!li.checkVisibility()) continue;
    const row = getComputedStyle(li.querySelector(":scope > .row"));
    if (transparent(row.backgroundColor) === on) errs.push(`${id}: highlight=${!transparent(row.backgroundColor)}, selected=${on}`);
    const ring = row.outlineStyle !== "none";
    if (ring !== (li === ringed)) errs.push(`${id}: ring=${ring}, expected ${li === ringed}`);
    if (getComputedStyle(li).outlineStyle !== "none") errs.push(`${id}: the treeitem itself has an outline`);
  }
  return errs;
}

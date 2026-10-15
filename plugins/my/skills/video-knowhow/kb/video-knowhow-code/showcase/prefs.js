// prefs.js — the owner's current preferences, layered over the base design. Delete this file and its one script
// tag in index.html to return to the base look. It changes three things:
//   type     no stock monospace: the mono face becomes the display face (Helvetica Neue), in the frames and in
//            the preview page
//   shelves  no eyebrow labels: each shelf's name leads its row on the items' baseline instead of sitting small
//            above the line, and the "n of 4" counter under the line goes
//   corners  no corner labels: the name, section, beat and frame counter at the top of the frame go
(function () {
  TOKENS.font.mono = TOKENS.font.display;
  TOKENS.faces = TOKENS.faces.filter(f => !f.includes('Menlo'));
  TOKENS.shelfLabel = 'row';
  TOKENS.hud = false;
  if (typeof document !== 'undefined') document.documentElement.style.fontFamily = TOKENS.font.display;
})();

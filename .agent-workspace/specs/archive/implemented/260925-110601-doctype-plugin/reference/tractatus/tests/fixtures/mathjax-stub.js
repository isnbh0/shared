(() => {
  const mode = window.__stubMode ?? "ok";
  const config = window.MathJax;
  window.__stubConfig = JSON.parse(JSON.stringify(config));
  // Run the page's ready() against a fake startup to capture the TeX post-filters it installs.
  const postFilters = (window.__stubPostFilters = []);
  window.MathJax = { startup: { defaultReady() {}, input: [{ postFilters: { add: (f, p) => postFilters.push([f, p]) } }] } };
  config.startup.ready();
  const calls = (window.__stubCalls = {});
  if (mode === "stall") { window.MathJax = { ...config, startup: { promise: new Promise(() => {}) } }; return; }
  if (mode === "nopromise") { window.MathJax = { ...config, startup: {} }; return; }
  window.MathJax = {
    ...config,
    startup: { promise: Promise.resolve() },
    getMetricsFor: () => ({}),
    chtmlStylesheet: () => Object.assign(document.createElement("style"), { id: "MJX-CHTML-styles" }),
    tex2chtmlPromise: async (tex) => {
      calls[tex] = (calls[tex] ?? 0) + 1;
      if (mode === "reject" && tex === "aRb") throw new Error("stub rejection");
      const out = document.createElement("mjx-container");
      if (mode === "merror" && tex === "aRb") out.append(document.createElement("mjx-merror"));
      else out.textContent = `[${tex}]`;
      return out;
    },
  };
})();

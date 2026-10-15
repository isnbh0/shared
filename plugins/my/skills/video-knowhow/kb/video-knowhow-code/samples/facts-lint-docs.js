// facts-lint-docs.js — one registry of the production's shared values, read from the modules that own them; pins
// that fail when a literal copy elsewhere drifts from its value; and generated doc regions, rewritten from the
// registry and checked for staleness.
// When you need it: the same number (a tempo, a margin, a loudness target, a cut's beat) lives in the score, the
// page, QA and the docs, and an edit to one copy must stop the build instead of shipping a contradiction.
// Source: generalized from the source production's facts registry, lint pins, and generated-doc
// checks.
// Generalized: the config block below is an example to edit (modules, facts, pins, docs, derived view). Left out:
// PENDING facts (a literal standing in until its export exists, with shape fitting), lint's declOf lookup (a probe
// there resolves the other names its expression uses from the same file), cross-file agreement checks, --strict.
// Put it at the project root. A region in a doc: <!-- gen:NAME|mods -->text<!-- /gen -->, NAME a dotted path
// into the view, mods any of |and |1 |code |- |– (list with "and", one decimal, backticks, the range dash).
// node facts-lint-docs.js           pins and stale regions; exits 1 on any ERROR
// node facts-lint-docs.js --write   rewrites stale regions      node facts-lint-docs.js --json   prints the facts
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const DIR = __dirname;

// ---- config (example)
const MODULES = { T: './timeline.js', EV: './score-events.json' };     // export prefixes and the files that own them
// key: the export (dotted; a [k] segment maps the rest over a list); at: where the value is used; by: who reads
// it; read: reshape the export to the value used here. An export that is missing is an error.
const EXPORTS = {
  'T.BPM': { at: ['audio.js BPM'], by: ['README.md'] },
  'T.SAFE': { read: s => ({ x0: s.x0, x1: s.x1, y0: s.y0, y1: s.y1 }), at: ['page.js'], by: ['README.md'] },
  'EV.kicks': { at: ['page.js pulse'], by: ['qa_av.py sync'] },
};
// A literal elsewhere that stands for a fact: the expression right after `anchor` in `file`, evaluated.
const PINS = [{ key: 'T.BPM', where: 'audio.js BPM', file: 'audio.js', anchor: /const BPM = / }];
const DOCS = { 'README.md': '–' };                                    // docs with regions, and each one's range dash
const VIEW = F => ({ margins: { x: { b0: F['T.SAFE'].x0, b1: F['T.SAFE'].x1 } }, kicks: F['EV.kicks'].length });

// ---- facts
const dig = (v, p) => {
  if (!p.length) return v;
  const [s, ...more] = p, each = s.endsWith('[k]'), k = each ? s.slice(0, -3) : s;
  if (v == null || !(k in Object(v))) return undefined;
  if (!each) return dig(v[k], more);
  const all = Array.isArray(v[k]) ? v[k].map(x => dig(x, more)) : [undefined];
  return all.includes(undefined) ? undefined : all;
};
function exported(key) {
  const [mod, ...p] = key.split('.');
  let m;
  try { m = require(path.resolve(DIR, MODULES[mod])); } catch { return undefined; }
  return dig(m, p);
}
const FACTS = {};
for (const [key, e] of Object.entries(EXPORTS)) {
  const x = exported(key);
  if (x === undefined) throw new Error(`facts: ${MODULES[key.split('.')[0]]} doesn't export ${key.split('.').slice(1).join('.')}`);
  FACTS[key] = (e.read || (y => y))(x);
}
const nest = F => Object.entries(F).reduce((o, [k, v]) => {
  const p = k.split('.'), last = p.pop();
  p.reduce((n, s) => (n[s] ||= {}), o)[last] = v;
  return o;
}, {});
const V = { ...nest(FACTS), ...VIEW(FACTS) };

// ---- pins
const num = x => String(Number((+x).toFixed(4)));
const show = v => (typeof v === 'number' ? num(v) : Array.isArray(v) ? `[${v.map(show).join(', ')}]`
  : v && typeof v === 'object' ? `{${Object.entries(v).map(([k, x]) => `${k}: ${show(x)}`).join(', ')}}` : JSON.stringify(v));
function same(a, b, tol = 1e-9) {
  if (typeof a === 'number' && typeof b === 'number') return Math.abs(a - b) <= tol + 1e-9;
  if (a && b && typeof a === 'object' && typeof b === 'object')
    return Object.keys(a).length === Object.keys(b).length && Object.keys(a).every(k => same(a[k], b[k], tol));
  return a === b;
}
// The source of the expression at i: up to a ; or , outside brackets, a newline the next line doesn't continue
// (.map(...), an operator), or the bracket that closes around it. Strings and comments are stepped over.
function exprAt(s, i) {
  const start = i, more = /^\s*(?:\.(?!\.)|\?|:|[-+*%&|]|\/(?![/*]))/;
  let depth = 0;
  for (; i < s.length; i++) {
    const c = s[i];
    if (c === '/' && s[i + 1] === '/') { i = s.indexOf('\n', i) - 1; continue; }
    if (c === '/' && s[i + 1] === '*') { i = s.indexOf('*/', i) + 1; continue; }
    if (c === '"' || c === "'" || c === '`') { while (s[++i] !== c) if (s[i] === '\\') i++; continue; }
    if ('([{'.includes(c)) depth++;
    else if (')]}'.includes(c) && --depth < 0) break;
    else if (depth === 0 && (';,'.includes(c) || (c === '\n' && !more.test(s.slice(i + 1, i + 40))))) break;
  }
  return s.slice(start, i).trim();
}
function probe(file, anchor, ctx = {}) {   // the literal's value, evaluated as an expression with ctx's names
  const s = fs.readFileSync(path.join(DIR, file), 'utf8'), m = anchor.exec(s);
  if (!m) throw new Error(`${file}: nothing matches ${anchor}`);
  return vm.runInContext(`(${exprAt(s, m.index + m[0].length)})`, vm.createContext({ ...ctx }));
}
const pins = () => PINS.flatMap(({ key, field, where, file, anchor, ctx }) => {
  let have;
  try { have = probe(file, anchor, ctx); } catch (e) { return [`WARN pin: ${key} probe failed: ${e.message}`]; }
  const want = field ? field.split('.').reduce((v, k) => v[k], FACTS[key]) : FACTS[key];
  return same(have, want) ? [] : [`ERROR pin: ${where} is ${show(have)}, ${key}${field ? '.' + field : ''} is ${show(want)}: read it there`];
});

// ---- generated doc regions
const REGION = /<!-- gen:(\S+?) -->([\s\S]*?)<!-- \/gen -->/g;
function fmt(v, mods, dash) {
  if (typeof v === 'number') return mods['1'] ? v.toFixed(1) : num(v);
  if (typeof v === 'string') return v;
  if (Array.isArray(v)) { const a = v.map(x => fmt(x, mods, dash)); return mods.and && a.length > 1 ? a.slice(0, -1).join(', ') + ' and ' + a.at(-1) : a.join(', '); }
  if (v && 'b0' in v && 'b1' in v && Object.keys(v).length === 2) return fmt(v.b0, mods, dash) + dash + fmt(v.b1, mods, dash);
  throw new Error(`can't format ${JSON.stringify(v)}`);
}
function render(name, dash) {
  const [key, ...ms] = name.split('|'), mods = {};
  for (const m of ms) (m === '-' || m === '–') ? (dash = m) : (mods[m] = true);
  const v = key.split('.').reduce((o, k) => { if (o == null || !(k in Object(o))) throw new Error(`no fact ${key}`); return o[k]; }, V);
  return mods.code ? '`' + fmt(v, mods, dash) + '`' : fmt(v, mods, dash);
}
function regions() {                       // [{ doc, name, have, want }]; unbalanced or nested markers throw
  return Object.entries(DOCS).flatMap(([doc, dash]) => {
    const text = fs.readFileSync(path.join(DIR, doc), 'utf8');
    const opens = (text.match(/<!-- gen:/g) || []).length, closes = (text.match(/<!-- \/gen -->/g) || []).length;
    if (opens !== closes) throw new Error(`${doc}: ${opens} gen markers open, ${closes} close`);
    return [...text.matchAll(REGION)].map(m => {
      if (m[2].includes('<!-- gen:')) throw new Error(`${doc}: gen:${m[1]} is not closed before the next region`);
      return { doc, name: m[1], have: m[2], want: render(m[1], dash) };
    });
  });
}
const check = () => regions().filter(r => r.have !== r.want).map(r => `ERROR docs: ${r.doc} gen:${r.name} is stale (${r.have} -> ${r.want})`);
function write() {
  const all = regions();
  for (const doc of Object.keys(DOCS)) {
    const file = path.join(DIR, doc), want = all.filter(r => r.doc === doc);
    let i = 0;
    if (want.some(r => r.have !== r.want)) fs.writeFileSync(file, fs.readFileSync(file, 'utf8').replace(REGION, (m, name) => `<!-- gen:${name} -->${want[i++].want}<!-- /gen -->`));
  }
}

module.exports = { FACTS, V, exprAt, probe, same, pins, regions, check, write };

if (require.main === module) {
  if (process.argv.includes('--json')) process.stdout.write(JSON.stringify(FACTS) + '\n');
  else if (process.argv.includes('--write')) write();
  else {
    const found = [...pins(), ...check()];
    for (const l of found) console.log(l);
    console.log(`${found.filter(l => l.startsWith('ERROR')).length} errors`);
    process.exitCode = found.some(l => l.startsWith('ERROR')) ? 1 : 0;
  }
}

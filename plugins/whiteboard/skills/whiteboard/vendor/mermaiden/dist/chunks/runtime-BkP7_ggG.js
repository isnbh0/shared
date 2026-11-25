import e from "mermaid";
//#region src/mermaid/transaction.ts
var t = Promise.resolve();
function n(e) {
	let n = t.then(e, e);
	return t = n.then(() => void 0, () => void 0), n;
}
//#endregion
//#region src/mermaid/runtime.ts
var r = class extends Error {
	stage;
	cause;
	constructor(e, t) {
		super(`Mermaid transaction failed during ${e}.`, { cause: t }), this.name = "MermaidTransactionFailure", this.stage = e, this.cause = t;
	}
};
function i(e) {
	e?.throwIfAborted();
}
function a() {
	try {
		e.mermaidAPI.reset();
	} catch {}
}
function o(e) {
	try {
		i(e);
	} catch (e) {
		throw a(), e;
	}
}
function s(e) {
	return typeof e == "object" && e || typeof e == "function" ? typeof e.then == "function" : !1;
}
function c(e, t, n, o) {
	throw o && a(), i(n), new r(e, t);
}
async function l(t, n, r, a, o) {
	let c;
	try {
		c = a.appliesTo(n);
	} catch (e) {
		return i(o), {
			status: "failed",
			reason: e
		};
	}
	if (!c) return { status: "not-applicable" };
	let l;
	try {
		l = (await e.mermaidAPI.getDiagramFromText(t)).db;
	} catch (e) {
		return i(o), {
			status: "failed",
			reason: e
		};
	}
	i(o);
	try {
		let e = a.inspect({
			diagramType: n,
			database: l,
			svg: r
		});
		if (s(e)) throw TypeError("Mermaid inspectors must return a synchronous value.");
		return {
			status: "available",
			value: e
		};
	} catch (e) {
		return i(o), {
			status: "failed",
			reason: e
		};
	}
}
function u(t = {}) {
	let s, u = () => (s ??= Promise.resolve().then(() => {
		t.layoutLoaders && e.registerLayoutLoaders(t.layoutLoaders);
	}), s), d = async (e) => {
		try {
			await u();
		} catch (t) {
			throw i(e), new r("setup", t);
		}
		i(e);
	};
	return {
		async validate(t) {
			return i(t.signal), n(async () => {
				i(t.signal), await d(t.signal);
				try {
					e.initialize(t.config);
				} catch (e) {
					c("initialization", e, t.signal, !0);
				}
				o(t.signal);
				try {
					await e.parse(t.source);
				} catch (e) {
					c("parse", e, t.signal, !0);
				}
				try {
					i(t.signal);
				} catch (e) {
					throw a(), e;
				}
			});
		},
		async render(t) {
			return i(t.signal), n(async () => {
				i(t.signal), await d(t.signal);
				let n = t.config, r = n !== void 0;
				if (r) {
					try {
						e.initialize(n);
					} catch (e) {
						c("initialization", e, t.signal, !0);
					}
					o(t.signal);
				}
				let s;
				try {
					s = await e.render(t.id, t.source, t.container);
				} catch (e) {
					c("render", e, t.signal, r);
				}
				try {
					i(t.signal);
				} catch (e) {
					throw r && a(), e;
				}
				if (!t.inspector) return { result: s };
				let u = await l(t.source, s.diagramType, s.svg, t.inspector, t.signal);
				return i(t.signal), {
					result: s,
					inspection: u
				};
			});
		}
	};
}
var d = u();
//#endregion
export { n as i, u as n, d as r, r as t };

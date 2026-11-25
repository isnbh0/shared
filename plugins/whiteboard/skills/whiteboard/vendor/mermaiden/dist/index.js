import { i as e, n as t, r as n, t as r } from "./chunks/runtime-BkP7_ggG.js";
import i from "mermaid";
export * from "mermaid";
//#region src/mermaid/svgDocument.ts
var a = "http://www.w3.org/1999/xlink";
function o(e) {
	let t = e.replace(/<br(\s[^/>]*)?>/gi, (e, t = "") => `<br${t}/>`);
	return t = /\bxlink:/.test(t) && !/<svg\b[^>]*\bxmlns:xlink=/.test(t) ? t.replace(/<svg\b/, `<svg xmlns:xlink="${a}"`) : t, new DOMParser().parseFromString(t, "image/svg+xml");
}
//#endregion
//#region src/semantics/flowchart.ts
var s = /* @__PURE__ */ new Set([
	"flowchart",
	"flowchart-v2",
	"flowchart-elk",
	"graph"
]), c = (e) => Object.freeze({
	severity: "warning",
	message: e
}), l = (e) => Object.freeze(e.map(c)), u = (e) => {
	if (typeof e == "string") return e;
	try {
		if (e && typeof e == "object" && "text" in e && typeof e.text == "string") return e.text;
	} catch {
		return "";
	}
	return "";
};
function d(e) {
	if (!e || typeof e != "object") return;
	let t = e.getData;
	if (typeof t != "function") return;
	let n = t.call(e);
	if (!n || typeof n != "object") return;
	let r = n;
	return Array.isArray(r.nodes) && Array.isArray(r.edges) ? {
		nodes: r.nodes,
		edges: r.edges
	} : void 0;
}
function f(e, t) {
	if (typeof e == "object" && e || typeof e == "function") try {
		return e[t];
	} catch {
		return;
	}
}
var p = (e) => Object.freeze({
	id: f(e, "id"),
	domId: f(e, "domId"),
	label: f(e, "label"),
	isGroup: f(e, "isGroup")
}), m = (e) => Object.freeze({
	id: f(e, "id"),
	start: f(e, "start"),
	end: f(e, "end"),
	thickness: f(e, "thickness"),
	pattern: f(e, "pattern"),
	stroke: f(e, "stroke")
});
function h(e) {
	return [
		e.thickness,
		e.pattern,
		e.stroke
	].some((e) => typeof e == "string" && e.toLowerCase() === "invisible");
}
function g(e, t) {
	return Object.freeze({
		kind: "unavailable",
		diagramType: e,
		diagnostics: l([t])
	});
}
function _(e) {
	try {
		let t = o(e);
		return t.querySelector("parsererror") ? void 0 : t;
	} catch {
		return;
	}
}
function v(e) {
	let t;
	try {
		t = d(e.database);
	} catch {
		return g(e.diagramType, "Supported Mermaid database access failed.");
	}
	if (!t) return g(e.diagramType, "Supported Mermaid database shape was unavailable.");
	let n = [], r = t.nodes.map(p), i = r.filter(({ isGroup: e }) => e !== !0), a = new Set(r.filter(({ isGroup: e }) => e === !0).map(({ id: e }) => e).filter((e) => typeof e == "string")), o = t.edges.map(m), s = /* @__PURE__ */ new Map(), c = /* @__PURE__ */ new Map();
	for (let e of i) typeof e.id == "string" && s.set(e.id, (s.get(e.id) ?? 0) + 1), typeof e.domId == "string" && c.set(e.domId, (c.get(e.domId) ?? 0) + 1);
	let f = [], v = /* @__PURE__ */ new Set(), y = /* @__PURE__ */ new Map();
	for (let e of i) {
		if (typeof e.id != "string") {
			n.push("An ordinary node lacked a string id and was excluded.");
			continue;
		}
		if (s.get(e.id) !== 1) {
			n.push(`Node ${e.id} had a duplicate logical id and was excluded.`);
			continue;
		}
		let t = Object.freeze({
			id: e.id,
			label: u(e.label) || e.id
		});
		v.add(e.id), y.set(e.id, e), f.push(t);
	}
	let b = /* @__PURE__ */ new Map();
	for (let e of o) typeof e.id == "string" && b.set(e.id, (b.get(e.id) ?? 0) + 1);
	let x = [], S = 0;
	for (let e of o) {
		if (typeof e.id != "string" || typeof e.start != "string" || typeof e.end != "string" || b.get(e.id) !== 1) {
			n.push("A malformed or duplicate edge was excluded.");
			continue;
		}
		let t = h(e);
		if (!v.has(e.start) || !v.has(e.end)) {
			[e.start, e.end].every((e) => v.has(e) || a.has(e)) ? t || (S += 1) : n.push(`Edge ${e.id} had an endpoint outside the logical flowchart model and was excluded.`);
			continue;
		}
		x.push(Object.freeze({
			id: e.id,
			start: e.start,
			end: e.end,
			visible: !t
		}));
	}
	if (S > 0) {
		let e = S !== 1;
		n.push(`${S} visible edge${e ? "s" : ""} connect${e ? "" : "s"} to a subgraph container and ${e ? "are" : "is"} not part of relationship highlighting.`);
	}
	let C = _(e.svg), w = [], T = [];
	if (!C) n.push("Rendered SVG could not be inspected; rendered mappings were omitted.");
	else {
		let e = C.documentElement.id, t = [...C.querySelectorAll("[id]")];
		for (let r of f) {
			let i = y.get(r.id);
			if (typeof i?.domId != "string") {
				n.push(`Node ${r.id} lacked a string rendered domId; its rendered mapping was omitted.`);
				continue;
			}
			if (c.get(i.domId) !== 1) {
				n.push(`Node ${r.id} did not map uniquely to the rendered SVG; its rendered mapping was omitted.`);
				continue;
			}
			let a = /* @__PURE__ */ new Set([i.domId, ...e ? [`${e}-${i.domId}`] : []]), o = t.filter((e) => a.has(e.id)), s = o.length === 1 ? o[0]?.id : void 0;
			if (!s) {
				n.push(`Node ${r.id} did not map uniquely to the rendered SVG; its rendered mapping was omitted.`);
				continue;
			}
			w.push(Object.freeze({
				nodeId: r.id,
				elementId: s
			}));
		}
		let r = [...C.querySelectorAll("[data-edge='true'][data-id]")];
		for (let e of x) {
			if (r.filter((t) => t.getAttribute("data-id") === e.id).length !== 1) {
				n.push(`Edge ${e.id} did not map uniquely to the rendered SVG; its rendered mapping was omitted.`);
				continue;
			}
			T.push(Object.freeze({
				edgeId: e.id,
				dataId: e.id
			}));
		}
	}
	return Object.freeze({
		kind: "flowchart",
		diagramType: e.diagramType,
		model: Object.freeze({
			nodes: Object.freeze(f),
			edges: Object.freeze(x)
		}),
		rendered: Object.freeze({
			nodes: Object.freeze(w),
			edges: Object.freeze(T)
		}),
		diagnostics: l(n)
	});
}
function y(e) {
	return s.has(e) ? "flowchart" : void 0;
}
var b = {
	appliesTo: (e) => y(e) !== void 0,
	inspect: v
}, x = Object.freeze(/* @__PURE__ */ "SOLID.DOTTED.SOLID_CROSS.DOTTED_CROSS.SOLID_OPEN.DOTTED_OPEN.SOLID_POINT.DOTTED_POINT.BIDIRECTIONAL_SOLID.BIDIRECTIONAL_DOTTED.SOLID_TOP.SOLID_BOTTOM.STICK_TOP.STICK_BOTTOM.SOLID_ARROW_TOP_REVERSE.SOLID_ARROW_BOTTOM_REVERSE.STICK_ARROW_TOP_REVERSE.STICK_ARROW_BOTTOM_REVERSE.SOLID_TOP_DOTTED.SOLID_BOTTOM_DOTTED.STICK_TOP_DOTTED.STICK_BOTTOM_DOTTED.SOLID_ARROW_TOP_REVERSE_DOTTED.SOLID_ARROW_BOTTOM_REVERSE_DOTTED.STICK_ARROW_TOP_REVERSE_DOTTED.STICK_ARROW_BOTTOM_REVERSE_DOTTED".split(".")), S = Object.freeze({
	NOTE: 2,
	LOOP_START: 10,
	LOOP_END: 11,
	ALT_START: 12,
	ALT_ELSE: 13,
	ALT_END: 14,
	OPT_START: 15,
	OPT_END: 16,
	ACTIVE_START: 17,
	ACTIVE_END: 18,
	PAR_START: 19,
	PAR_AND: 20,
	PAR_END: 21,
	RECT_START: 22,
	RECT_END: 23,
	AUTONUMBER: 26,
	CRITICAL_START: 27,
	CRITICAL_OPTION: 28,
	CRITICAL_END: 29,
	BREAK_START: 30,
	BREAK_END: 31,
	PAR_OVER_START: 32,
	CENTRAL_CONNECTION: 59,
	CENTRAL_CONNECTION_REVERSE: 60,
	CENTRAL_CONNECTION_DUAL: 61
}), C = Object.freeze({
	amp: "&",
	apos: "'",
	gt: ">",
	lt: "<",
	num: "#",
	quot: "\"",
	semi: ";"
});
function w(e) {
	return e.replace(/\uFB02\xB0(\xB0?)(\w+)\xB6\xDF/g, (e, t, n) => {
		if (t === "°") {
			if (!/^\+?\d+$/.test(n)) return e;
			let t = Number(n);
			return Number.isSafeInteger(t) && t >= 0 && t <= 1114111 && !(t >= 55296 && t <= 57343) ? String.fromCodePoint(t) : e;
		}
		return C[n] ?? e;
	});
}
var T = (e) => Object.freeze({
	severity: "warning",
	message: e
}), E = (e) => Object.freeze(e.map(T));
function D(e, t) {
	if (typeof e == "object" && e || typeof e == "function") try {
		return e[t];
	} catch {
		return;
	}
}
function O(e, t) {
	let n = D(e, t);
	if (typeof n == "function") return n.call(e);
}
function k(e, t) {
	return Object.freeze({
		kind: "unavailable",
		diagramType: e,
		diagnostics: E([t])
	});
}
function A(e, t) {
	if (t === e) return;
	let n = [], r = t;
	for (; r !== e;) {
		let e = r.parentElement;
		if (!e) return;
		let t = Array.prototype.indexOf.call(e.children, r);
		if (t < 0) return;
		n.push(t), r = e;
	}
	return Object.freeze(n.reverse());
}
function ee(e, t) {
	if (t === e) return;
	if (t.tagName.toLowerCase() === "g") return t;
	let n = t.parentElement;
	if (!n || n === e || n.tagName.toLowerCase() !== "g") return t;
	let r = [...n.querySelectorAll("[name].actor-bottom")];
	return r.length === 1 && r[0] === t ? n : t;
}
function j(e, t) {
	if (new Set(t).size !== t.length) return;
	for (let e of t) for (let n of t) if (e !== n && e.contains(n)) return;
	let n = t.map((t) => A(e, t));
	return n.every((e) => e !== void 0) ? Object.freeze(n) : void 0;
}
function M(e) {
	let t = O(e, "getActors");
	if (!(t instanceof Map)) return;
	let n = [];
	for (let [e, r] of t) {
		let t = D(r, "description");
		if (typeof e != "string" || typeof t != "string") return;
		n.push(Object.freeze({
			id: e,
			label: w(t)
		}));
	}
	return n;
}
function N(e) {
	let t = O(e, "getMessages"), n = D(e, "LINETYPE");
	if (!Array.isArray(t) || !n || typeof n != "object") return;
	let r = /* @__PURE__ */ new Set();
	for (let e of x) {
		let t = D(n, e);
		if (typeof t != "number") return;
		r.add(t);
	}
	let i = [];
	for (let e of t) {
		let t = D(e, "type");
		if (typeof t != "number" || !r.has(t)) continue;
		let n = D(e, "id"), a = D(e, "from"), o = D(e, "to"), s = D(e, "message");
		if (typeof n != "string" || typeof a != "string" || typeof o != "string" || typeof s != "string") return;
		i.push(Object.freeze({
			id: n,
			from: a,
			to: o,
			label: w(s),
			type: t
		}));
	}
	return i;
}
function P(e) {
	let t = O(e, "getMessages");
	if (Array.isArray(t)) return t.map((e) => {
		let t = D(e, "id"), n = D(e, "type"), r = D(e, "message");
		if (typeof t != "string" || typeof n != "number") throw Error("invalid sequence event");
		return Object.freeze({
			id: t,
			type: n,
			from: typeof D(e, "from") == "string" ? D(e, "from") : void 0,
			to: typeof D(e, "to") == "string" ? D(e, "to") : void 0,
			label: typeof r == "string" ? w(r) : ""
		});
	});
}
function te(e, t) {
	return t.has(e) ? "message" : e === S.NOTE ? "note" : e === S.ACTIVE_START ? "activation-start" : e === S.ACTIVE_END ? "activation-end" : [
		S.CENTRAL_CONNECTION,
		S.CENTRAL_CONNECTION_REVERSE,
		S.CENTRAL_CONNECTION_DUAL
	].includes(e) ? "central-connection" : [
		S.LOOP_START,
		S.ALT_START,
		S.OPT_START,
		S.PAR_START,
		S.PAR_OVER_START,
		S.CRITICAL_START,
		S.BREAK_START
	].includes(e) ? "fragment-open" : [
		S.ALT_ELSE,
		S.PAR_AND,
		S.CRITICAL_OPTION
	].includes(e) ? "fragment-branch" : [
		S.LOOP_END,
		S.ALT_END,
		S.OPT_END,
		S.PAR_END,
		S.CRITICAL_END,
		S.BREAK_END
	].includes(e) ? "fragment-close" : e === S.RECT_START ? "rect-open" : e === S.RECT_END ? "rect-close" : e === S.AUTONUMBER ? "autonumber" : "unknown";
}
function F(e, t) {
	return Object.freeze({
		completeDisclosure: e,
		diagnostics: Object.freeze(t.map((e) => Object.freeze({
			code: e.code,
			eventIds: Object.freeze([...e.eventIds])
		})))
	});
}
var I = (e, t, n) => e.getAttribute(t) === n;
function L(e) {
	return e.replace(/<br\s*\/?>/gi, "").replace(/<[^>]*>/g, "").replace(/\s+/g, "");
}
function ne(e, t) {
	let n = [e], r = (e) => e?.tagName.toLowerCase() === "g" && e.children.length > 0 && [...e.children].every((e) => e.tagName.toLowerCase() === "circle"), i = e.previousElementSibling;
	if (r(i) && (n.unshift(i), i = i.previousElementSibling), !i || !(i.classList.contains("messageText") || i.tagName.toLowerCase() === "foreignobject") || t !== "" && !t.includes("<") && L(i.textContent ?? "") !== L(t)) return;
	n.unshift(i);
	let a = e.nextElementSibling;
	r(a) && (n.push(a), a = a.nextElementSibling);
	let o = a?.nextElementSibling;
	if (a?.tagName.toLowerCase() === "line" && a.getAttribute("stroke-width") === "0" && o?.classList.contains("sequenceNumber")) n.push(a, o);
	else if (o?.classList.contains("sequenceNumber")) return;
	return n;
}
function R(e) {
	let t, n, r;
	try {
		t = M(e.database), n = N(e.database), r = P(e.database);
	} catch {
		return k(e.diagramType, "Supported Mermaid sequence database access failed.");
	}
	if (!t || !n || !r) return k(e.diagramType, "Supported Mermaid sequence database shape was unavailable.");
	let i = D(e.database, "LINETYPE");
	if (!i || typeof i != "object" || Object.entries(S).some(([e, t]) => D(i, e) !== t)) return k(e.diagramType, "Pinned Mermaid sequence event table did not match 12.0.0.");
	let a = new Set(x.map((e) => D(i, e)).filter((e) => typeof e == "number")), s = [], c = new Set(t.map(({ id: e }) => e));
	if (c.size !== t.length) return k(e.diagramType, "Sequence participants did not have unique identifiers.");
	let l = /* @__PURE__ */ new Set(), u = [], d = [];
	for (let e of n) {
		if (l.has(e.id) || !c.has(e.from) || !c.has(e.to)) {
			s.push("A sequence message had duplicate identity or an unknown endpoint and was excluded.");
			continue;
		}
		l.add(e.id), d.push(e), u.push(Object.freeze({
			id: e.id,
			from: e.from,
			to: e.to,
			label: e.label,
			order: u.length
		}));
	}
	let f = t.map(({ id: e, label: t }) => Object.freeze({
		id: e,
		label: t
	})), p = /* @__PURE__ */ new Map(), m = /* @__PURE__ */ new Map(), h = 0;
	r.forEach((e, t) => {
		a.has(e.type) && m.set(t, h++);
	});
	let g = (e) => {
		for (let t = e; t < r.length; t += 1) {
			let e = m.get(t);
			if (e !== void 0) return e;
		}
		return u.length > 0 ? u.length - 1 : null;
	}, _ = r.map((e, t) => {
		let n = p.get(e.id) ?? 0;
		p.set(e.id, n + 1);
		let r = te(e.type, a), i = m.get(t), o = Object.freeze([...new Set([e.from, e.to].filter((e) => typeof e == "string"))]);
		return {
			id: `sequence-event-${e.id}-${n}`,
			rawId: e.id,
			kind: r,
			ordinal: t,
			participants: o,
			messageId: i === void 0 ? void 0 : u[i]?.id,
			revealAtMessage: i ?? g(t),
			interval: void 0
		};
	}), v = /* @__PURE__ */ new Map(), y = [], b = [];
	for (let e = 0; e < _.length; e += 1) {
		let t = _[e], n = r[e];
		if (t.kind === "activation-start" || t.kind === "central-connection") {
			let t = n.from ?? n.to ?? "", r = v.get(t) ?? [];
			r.push(e), v.set(t, r);
		} else if (t.kind === "activation-end") {
			let t = (v.get(n.from ?? "") ?? []).pop();
			t !== void 0 && b.push([t, e]);
		} else if (t.kind === "fragment-open" || t.kind === "rect-open") y.push(e);
		else if (t.kind === "fragment-close" || t.kind === "rect-close") {
			let t = y.pop();
			t !== void 0 && b.push([t, e]);
		}
	}
	for (let [e, t] of b) {
		let n = [...m].filter(([n]) => n > e && n < t).map(([, e]) => e), r = n[0] ?? g(t), i = n.at(-1) ?? r, a = Object.freeze({
			startEventId: _[e].id,
			endEventId: _[t].id,
			fromMessage: r,
			toMessage: i
		});
		_[e].interval = a, _[t].interval = a, _[e].revealAtMessage = r, _[t].revealAtMessage = i;
	}
	let C = Object.freeze(_.map((e) => Object.freeze(e))), w = [], T = (e, t) => w.push(Object.freeze({
		code: e,
		eventIds: Object.freeze([...t])
	})), A = O(e.database, "getBoxes");
	Array.isArray(A) && A.length > 0 && T("sequence-box-groups-unsupported", []);
	let L = O(e.database, "getCreatedActors"), R = O(e.database, "getDestroyedActors");
	(L instanceof Map && L.size > 0 || R instanceof Map && R.size > 0) && T("sequence-participant-lifecycle-unsupported", []);
	let z = C.filter((e) => r[e.ordinal]?.type === S.PAR_OVER_START).map(({ id: e }) => e);
	z.length > 0 && T("sequence-par-over-unsupported", z);
	let B = C.filter(({ kind: e }) => e === "unknown").map(({ id: e }) => e);
	B.length > 0 && T("sequence-event-mapping-incomplete", B);
	let V = [...v.values()].flat();
	V.length > 0 && T("sequence-activation-mapping-incomplete", V.map((e) => C[e].id)), y.length > 0 && T("sequence-event-mapping-incomplete", y.map((e) => C[e].id));
	let H;
	try {
		if (H = o(e.svg), H.querySelector("parsererror")) throw Error("invalid SVG");
	} catch {
		return Object.freeze({
			kind: "sequence",
			diagramType: e.diagramType,
			model: Object.freeze({
				participants: Object.freeze(f),
				messages: Object.freeze(u),
				events: C
			}),
			rendered: Object.freeze({
				participants: Object.freeze([]),
				messages: Object.freeze([]),
				content: Object.freeze([])
			}),
			capabilities: Object.freeze({ disclosure: F(!1, [...w, Object.freeze({
				code: "sequence-event-mapping-incomplete",
				eventIds: Object.freeze([])
			})]) }),
			diagnostics: E([...s, "Rendered SVG could not be inspected; rendered mappings were omitted."])
		});
	}
	let U = H.documentElement, W = [];
	for (let e of f) {
		let t = [...H.querySelectorAll("[data-et='participant'][data-id]")].filter((t) => I(t, "data-id", e.id)), n = [...H.querySelectorAll("[data-et='life-line'][data-id]")].filter((t) => I(t, "data-id", e.id)), r = [...H.querySelectorAll("[name]")].filter((t) => I(t, "name", e.id) && t.classList.contains("actor-bottom")), i = [...new Set(r.map((e) => ee(U, e)))].filter((e) => e !== void 0);
		if (t.length !== 1 || n.length !== 1 || i.length > 1) {
			s.push(`Participant ${e.id} did not map uniquely to the rendered SVG; its rendered mapping was omitted.`);
			continue;
		}
		let a = j(U, t), o = j(U, i), c = j(U, n);
		if (!a || !o || !c) {
			s.push(`Participant ${e.id} had invalid rendered references; its rendered mapping was omitted.`);
			continue;
		}
		W.push(Object.freeze({
			participantId: e.id,
			header: a,
			footer: o,
			lifeline: c
		}));
	}
	let G = [];
	for (let e = 0; e < d.length; e += 1) {
		let t = d[e], n = u[e];
		if (!t || !n) continue;
		let r = [...H.querySelectorAll("[data-et='message'][data-id]")].filter((e) => I(e, "data-id", `i${t.id}`) && I(e, "data-from", t.from) && I(e, "data-to", t.to)), i = r.length === 1 ? ne(r[0], t.label) : void 0, a = i ? j(U, i) : void 0;
		if (!a) {
			s.push(`Message ${n.id} did not map completely and uniquely to the rendered SVG; its rendered mapping was omitted.`);
			let e = C.find((e) => e.messageId === n.id);
			T("sequence-event-mapping-incomplete", e ? [e.id] : []);
			continue;
		}
		G.push(Object.freeze({
			messageId: n.id,
			elements: a
		}));
	}
	let K = [], q = /* @__PURE__ */ new Set(), J = (e, t, n, r = e.revealAtMessage, i = e.interval?.toMessage ?? e.revealAtMessage) => {
		let a = j(U, n);
		return !a || a.length === 0 ? !1 : (K.push(Object.freeze({
			eventId: e.id,
			role: t,
			elements: a,
			reveal: Object.freeze({
				fromMessage: r,
				toMessage: i
			})
		})), q.add(e.id), !0);
	};
	for (let e of C) if (e.kind === "note") {
		let t = [...H.querySelectorAll(`[data-et='note'][data-id='i${e.rawId}']`)];
		(t.length !== 1 || !J(e, "note", t)) && T("sequence-event-mapping-incomplete", [e.id]);
	}
	for (let e of C.filter((e) => e.kind === "fragment-close")) {
		let t = C.find((t) => t.interval?.endEventId === e.id && t.kind === "fragment-open");
		if (!t) continue;
		let n = [...H.querySelectorAll(`[data-et='control-structure'][data-id='i${e.rawId}']`)];
		if (n.length !== 1) {
			T("sequence-event-mapping-incomplete", [t.id, e.id]);
			continue;
		}
		let r = n[0], i = [...r.querySelectorAll(":scope > .loopLine")], a = [...r.querySelectorAll(":scope > .labelBox, :scope > .labelText, :scope > .loopText")];
		i[0] && a.push(i[0]), i[1] && a.push(i[1]), i[3] && a.push(i[3]), J(t, "fragment-opening", a, t.revealAtMessage, e.interval?.toMessage) || T("sequence-event-mapping-incomplete", [t.id]), (!i[2] || !J(e, "fragment-closing", [i[2]], e.revealAtMessage, e.revealAtMessage)) && T("sequence-event-mapping-incomplete", [e.id]);
		let o = C.filter((n) => n.kind !== "fragment-branch" || n.ordinal <= t.ordinal || n.ordinal >= e.ordinal ? !1 : b.filter(([e, t]) => e < n.ordinal && n.ordinal < t && C[e]?.kind === "fragment-open").sort((e, t) => t[0] - e[0])[0]?.[0] === t.ordinal), s = i.slice(4), c = [...r.querySelectorAll(":scope > .sectionTitle")];
		o.forEach((e, t) => {
			let n = [s[t], c[t]].filter((e) => e !== void 0);
			J(e, "fragment-branch", n) || T("sequence-event-mapping-incomplete", [e.id]);
		});
	}
	let Y = C.filter((e) => (e.kind === "activation-start" || e.kind === "central-connection") && e.interval), X = [...U.querySelectorAll("g")].filter((e) => [...e.children].some((e) => /^activation[0-2]$/.test(e.getAttribute("class") ?? "")));
	X.length === Y.length ? Y.forEach((e, t) => {
		J(e, "activation", [X[t]], e.interval.fromMessage, e.interval.toMessage) || T("sequence-activation-mapping-incomplete", [e.id]);
	}) : Y.length > 0 && T("sequence-activation-mapping-incomplete", Y.map(({ id: e }) => e));
	let Z = C.filter((e) => e.kind === "rect-close"), Q = [...U.querySelectorAll(":scope > rect.rect")].reverse();
	Q.length === Z.length ? Z.forEach((e, t) => {
		let n = C.find((t) => t.kind === "rect-open" && t.interval?.endEventId === e.id);
		(!n || !J(n, "rect-background", [Q[t]], n.interval?.fromMessage, n.interval?.toMessage)) && T("sequence-event-mapping-incomplete", [n?.id ?? e.id]);
	}) : Z.length > 0 && T("sequence-event-mapping-incomplete", Z.map(({ id: e }) => e));
	let $ = C.filter((e) => [
		"note",
		"activation-start",
		"central-connection",
		"fragment-open",
		"fragment-branch",
		"fragment-close",
		"rect-open"
	].includes(e.kind)).filter((e) => !q.has(e.id) && e.kind !== "activation-end").map(({ id: e }) => e);
	return $.length > 0 && !w.some(({ eventIds: e }) => $.every((t) => e.includes(t))) && T("sequence-event-mapping-incomplete", $), Object.freeze({
		kind: "sequence",
		diagramType: e.diagramType,
		model: Object.freeze({
			participants: Object.freeze(f),
			messages: Object.freeze(u),
			events: C
		}),
		rendered: Object.freeze({
			participants: Object.freeze(W),
			messages: Object.freeze(G),
			content: Object.freeze(K)
		}),
		capabilities: Object.freeze({ disclosure: F(w.length === 0, w) }),
		diagnostics: E(s)
	});
}
//#endregion
//#region src/semantics/renderer.ts
var z = Object.freeze([b, {
	appliesTo: (e) => e === "sequence",
	inspect: R
}]);
function B(e) {
	return Object.freeze({
		kind: "unsupported",
		diagramType: e,
		diagnostics: Object.freeze([])
	});
}
function V(e) {
	let t = Object.freeze({
		severity: "warning",
		message: "Semantic inspection was unavailable."
	});
	return Object.freeze({
		kind: "unavailable",
		diagramType: e,
		diagnostics: Object.freeze([t])
	});
}
function H() {
	let e;
	return {
		appliesTo(t) {
			return e = z.find((e) => e.appliesTo(t)), e !== void 0;
		},
		inspect(t) {
			if (!e) throw Error("No semantic adapter was selected for this diagram type.");
			return e.inspect(t);
		}
	};
}
function U(e = {}) {
	let n = t(e);
	return {
		validate: (e) => n.validate(e),
		async renderWithSemantics(e) {
			let t = await n.render({
				id: e.id,
				source: e.source,
				...e.container ? { container: e.container } : {},
				...e.config ? { config: e.config } : {},
				...e.signal ? { signal: e.signal } : {},
				inspector: H()
			}), r = t.inspection, i = r?.status === "available" ? r.value : r?.status === "not-applicable" ? B(t.result.diagramType) : V(t.result.diagramType);
			return {
				...t.result,
				semantics: i
			};
		}
	};
}
var W = U();
function G(e) {
	return W.renderWithSemantics(e);
}
//#endregion
//#region src/semantics/sequenceContractFixtures.ts
var K = Object.freeze([
	Object.freeze({
		id: "ordered-note-activation-fragment",
		source: "sequenceDiagram\nparticipant A\nparticipant B\nNote over A,B: leading\nA->>+B: begin\nalt accepted\nB-->>A: yes\nelse rejected\nB-->>A: no\nend\ndeactivate B",
		expectedKinds: Object.freeze([
			"note",
			"message",
			"activation-start",
			"fragment-open",
			"message",
			"fragment-branch",
			"message",
			"fragment-close",
			"activation-end"
		]),
		completeDisclosure: !0,
		diagnosticCodes: Object.freeze([])
	}),
	Object.freeze({
		id: "participant-box-gap",
		source: "sequenceDiagram\nbox Team\nparticipant A\nparticipant B\nend\nA->>B: hello",
		expectedKinds: Object.freeze(["message"]),
		completeDisclosure: !1,
		diagnosticCodes: Object.freeze(["sequence-box-groups-unsupported"])
	}),
	Object.freeze({
		id: "repeated-notes-and-entities",
		source: "sequenceDiagram\nparticipant A\nparticipant B\nNote over A,B: same #amp; value\nA->>B: go\nNote over A,B: same #amp; value\nB-->>A: back\nNote right of B: trailing",
		expectedKinds: Object.freeze([
			"note",
			"message",
			"note",
			"message",
			"note"
		]),
		completeDisclosure: !0,
		diagnosticCodes: Object.freeze([])
	}),
	Object.freeze({
		id: "nested-activation",
		source: "sequenceDiagram\nparticipant A\nparticipant B\nactivate B\nactivate B\nA->>B: nested\ndeactivate B\ndeactivate B",
		expectedKinds: Object.freeze([
			"activation-start",
			"activation-start",
			"message",
			"activation-end",
			"activation-end"
		]),
		completeDisclosure: !0,
		diagnosticCodes: Object.freeze([])
	}),
	Object.freeze({
		id: "central-connection",
		source: "sequenceDiagram\nparticipant A\nparticipant B\nA()->>B: forward\nA->>()B: reverse\nA()<<->>()B: dual",
		expectedKinds: Object.freeze([
			"message",
			"central-connection",
			"message",
			"central-connection",
			"message",
			"central-connection",
			"central-connection"
		]),
		completeDisclosure: !1,
		diagnosticCodes: Object.freeze(["sequence-activation-mapping-incomplete"])
	}),
	Object.freeze({
		id: "participant-lifecycle-gap",
		source: "sequenceDiagram\nparticipant A\ncreate participant B\nA->>B: hello\ndestroy B\nB-->>A: bye",
		expectedKinds: Object.freeze(["message", "message"]),
		completeDisclosure: !1,
		diagnosticCodes: Object.freeze(["sequence-participant-lifecycle-unsupported"])
	}),
	Object.freeze({
		id: "rect-region",
		source: "sequenceDiagram\nparticipant A\nparticipant B\nrect rgb(230, 240, 255)\nA->>B: inside\nend",
		expectedKinds: Object.freeze([
			"rect-open",
			"message",
			"rect-close"
		]),
		completeDisclosure: !0,
		diagnosticCodes: Object.freeze([])
	}),
	Object.freeze({
		id: "supported-control-structures",
		source: "sequenceDiagram\nparticipant A\nparticipant B\nloop outer\nopt optional\nA->>B: one\nend\nend\npar left\nA->>B: two\nand right\nB-->>A: three\nend\ncritical must\nA->>B: four\noption fallback\nB-->>A: five\nend\nbreak stop\nA->>B: six\nend",
		expectedKinds: Object.freeze([
			"fragment-open",
			"fragment-open",
			"message",
			"fragment-close",
			"fragment-close",
			"fragment-open",
			"message",
			"fragment-branch",
			"message",
			"fragment-close",
			"fragment-open",
			"message",
			"fragment-branch",
			"message",
			"fragment-close",
			"fragment-open",
			"message",
			"fragment-close"
		]),
		completeDisclosure: !0,
		diagnosticCodes: Object.freeze([])
	}),
	Object.freeze({
		id: "par-over-gap",
		source: "sequenceDiagram\nparticipant A\nparticipant B\npar_over A,B\nA->>B: first\nand second\nB->>A: second\nend",
		expectedKinds: Object.freeze([
			"fragment-open",
			"message",
			"fragment-branch",
			"message",
			"fragment-close"
		]),
		completeDisclosure: !1,
		diagnosticCodes: Object.freeze(["sequence-par-over-unsupported"])
	})
]);
//#endregion
//#region src/index.ts
async function q(e, t, i) {
	try {
		let { result: r } = await n.render({
			id: e,
			source: t,
			...i ? { container: i } : {}
		});
		return r;
	} catch (e) {
		throw e instanceof r ? e.cause : e;
	}
}
async function J(t = { querySelector: ".mermaid" }) {
	return e(() => i.run(t));
}
var Y = {
	trace: 0,
	debug: 1,
	info: 2,
	warn: 3,
	error: 4,
	fatal: 5
};
function X(e) {
	let t = i.mermaidAPI.getConfig().logLevel;
	return (typeof t == "number" ? t : typeof t == "string" ? Y[t.toLowerCase()] ?? Y.fatal : Y.fatal) <= e;
}
async function Z(e, t, n) {
	X(Y.warn) && console.warn("mermaid.init is deprecated. Please use run instead."), e && i.initialize(e);
	let r = {
		querySelector: ".mermaid",
		...n ? { postRenderCallback: n } : {}
	};
	typeof t == "string" ? r.querySelector = t : t && (r.nodes = t instanceof HTMLElement ? [t] : t), await J(r);
}
function Q() {
	i.startOnLoad && i.mermaidAPI.getConfig().startOnLoad && J().catch((e) => {
		X(Y.error) && console.error("Mermaid failed to initialize", e);
	});
}
typeof document < "u" && (window.removeEventListener("load", i.contentLoaded, !1), window.addEventListener("load", Q, !1));
function $(e) {
	return Object.defineProperty(e, "parseError", {
		enumerable: !0,
		configurable: !0,
		get: () => i.parseError,
		set: (e) => {
			i.parseError = e;
		}
	}), e;
}
var re = $({
	get startOnLoad() {
		return i.startOnLoad;
	},
	set startOnLoad(e) {
		i.startOnLoad = e;
	},
	mermaidAPI: i.mermaidAPI,
	parse: i.parse,
	render: q,
	renderWithSemantics: G,
	init: Z,
	run: J,
	registerLayoutLoaders: i.registerLayoutLoaders,
	registerExternalDiagrams: i.registerExternalDiagrams,
	initialize: i.initialize,
	contentLoaded: Q,
	setParseErrorHandler: i.setParseErrorHandler,
	detectType: i.detectType,
	registerIconPacks: i.registerIconPacks,
	getRegisteredDiagramsMetadata: i.getRegisteredDiagramsMetadata
});
//#endregion
export { r as MermaidTransactionFailure, U as createSemanticRenderer, re as default, G as renderWithSemantics, K as sequenceContractFixtures };

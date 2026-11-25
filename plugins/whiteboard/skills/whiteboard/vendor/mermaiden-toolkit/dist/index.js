//#region src/sequence/geometry.ts
function e(e) {
	return [
		e.a,
		e.b,
		e.c,
		e.d,
		e.e,
		e.f
	].every(Number.isFinite);
}
function t(t) {
	return e(t) && t.a * t.d - t.b * t.c !== 0;
}
function n(n, r) {
	if (n.isConnected && r.isConnected && n.contains(r)) try {
		let i = n.getScreenCTM(), a = r.getScreenCTM();
		if (!i || !a || !t(i) || !t(a)) return;
		let o = i.inverse().multiply(a);
		return e(o) ? o : void 0;
	} catch {
		return;
	}
}
function r(e, t) {
	if (t.length === 0) return;
	let n = e;
	for (let e of t) {
		if (!Number.isInteger(e) || e < 0) return;
		let t = n.children.item(e);
		if (!t) return;
		n = t;
	}
	return n.namespaceURI === "http://www.w3.org/2000/svg" ? n : void 0;
}
function i(e, t) {
	let n = t.map((t) => r(e, t));
	return n.every((e) => e !== void 0) ? n : void 0;
}
function a(e, t) {
	let n = /* @__PURE__ */ new Set(), r = (e) => {
		for (let [t, r] of e.entries()) if (e.slice(t + 1).some((e) => e === r) || n.has(r)) return !1;
		for (let t of e) n.add(t);
		return !0;
	}, a = /* @__PURE__ */ new Map();
	for (let n of t.rendered.participants) {
		if (a.has(n.participantId)) return;
		let t = i(e, n.header), o = i(e, n.footer), s = i(e, n.lifeline);
		if (!t || !o || !s || !r([
			...t,
			...o,
			...s
		])) return;
		a.set(n.participantId, {
			id: n.participantId,
			header: t,
			footer: o,
			lifeline: s
		});
	}
	let o = /* @__PURE__ */ new Map();
	for (let n of t.rendered.messages) {
		if (o.has(n.messageId)) return;
		let t = i(e, n.elements);
		if (!t || t.length === 0 || !r(t)) return;
		o.set(n.messageId, {
			id: n.messageId,
			elements: t
		});
	}
	let s = /* @__PURE__ */ new Map();
	for (let n of t.rendered.content ?? []) {
		if (s.has(n.eventId)) return;
		let t = i(e, n.elements);
		if (!t || t.length === 0 || !r(t)) return;
		s.set(n.eventId, {
			eventId: n.eventId,
			role: n.role,
			elements: t,
			reveal: n.reveal
		});
	}
	return {
		svg: e,
		participants: a,
		messages: o,
		content: s
	};
}
function o(e, t) {
	let n = Math.max(e.x, t.x), r = Math.max(e.y, t.y), i = Math.min(e.x + e.width, t.x + t.width), a = Math.min(e.y + e.height, t.y + t.height), o = {
		x: n,
		y: r,
		width: i - n,
		height: a - r
	};
	return l(o, !0) && o.width > 0 && o.height > 0 ? o : void 0;
}
function s(e, t) {
	try {
		let r = e.getBBox(), i = Number.parseFloat(e.getAttribute("stroke-width") ?? "0"), a = Number.isFinite(i) && i > 0 ? i / 2 : 0;
		for (let n of [
			"marker-start",
			"marker-mid",
			"marker-end"
		]) {
			let r = /url\(\s*["']?#([^)'"\s]+)["']?\s*\)/.exec(e.getAttribute(n) ?? ""), o = r?.[1] ? [...t.querySelectorAll("marker[id]")].find((e) => e.id === r[1]) : void 0;
			if (!o) continue;
			let s = Number.parseFloat(o.getAttribute("markerWidth") ?? "3"), c = Number.parseFloat(o.getAttribute("markerHeight") ?? "3"), l = o.getAttribute("markerUnits") === "userSpaceOnUse" ? 1 : Math.max(i || 1, 1);
			Number.isFinite(s) && Number.isFinite(c) && (a = Math.max(a, s * l, c * l));
		}
		let o = n(t, e);
		if (!o || typeof t.createSVGPoint != "function") return;
		let s = [
			[r.x - a, r.y - a],
			[r.x + r.width + a, r.y - a],
			[r.x - a, r.y + r.height + a],
			[r.x + r.width + a, r.y + r.height + a]
		].map(([e = 0, n = 0]) => {
			let r = t.createSVGPoint();
			return r.x = e, r.y = n, r.matrixTransform(o);
		}), c = s.map((e) => e.x), u = s.map((e) => e.y), d = {
			x: Math.min(...c),
			y: Math.min(...u),
			width: Math.max(...c) - Math.min(...c),
			height: Math.max(...u) - Math.min(...u)
		};
		return l(d, !0) ? d : void 0;
	} catch {
		return;
	}
}
var c = s;
function l(e, t = !1) {
	return Object.values(e).every(Number.isFinite) && e.width >= 0 && e.height >= 0 && (t || e.width > 0 && e.height > 0);
}
function u(e) {
	if (e.length === 0 || e.some((e) => !l(e, !0))) return;
	let t = Math.min(...e.map((e) => e.x)), n = Math.min(...e.map((e) => e.y)), r = Math.max(...e.map((e) => e.x + e.width)), i = Math.max(...e.map((e) => e.y + e.height)), a = {
		x: t,
		y: n,
		width: r - t,
		height: i - n
	};
	return l(a) ? a : void 0;
}
function d(e, t) {
	let n = Math.max(0, Number.isFinite(t) ? t : 0), r = {
		x: e.x - n,
		y: e.y - n,
		width: e.width + n * 2,
		height: e.height + n * 2
	};
	return l(r) ? r : void 0;
}
function f(e, t, n = 0, r = 0) {
	if (![
		e.width,
		e.height,
		n,
		r
	].every(Number.isFinite) || e.width <= 0 || e.height <= 0 || !l(t) || n < 0 || r < 0) return;
	let i = Math.min(e.width / t.width, e.height / (t.height + n + r));
	if (!Number.isFinite(i) || i <= 0) return;
	let a = n * i, o = r * i;
	return {
		scale: i,
		topInset: a,
		bottomInset: o,
		x: (e.width - t.width * i) / 2 - t.x * i,
		y: a + (e.height - a - o - t.height * i) / 2 - t.y * i
	};
}
//#endregion
//#region src/sequence/projection.ts
var p = (e, t, n) => {
	let r = [];
	for (let i of e) {
		let e = t.get(i), a = e && n ? o(e, n) : e;
		a && r.push(a);
	}
	return r;
};
function m(e, t, n, r, i = !1) {
	let a = e.model.messages.length;
	if (a === 0 && (i = !0), !i && (!Number.isInteger(r) || r < 0 || r >= a)) return;
	let o = u([...n.values()]);
	if (!o) return;
	let s = /* @__PURE__ */ new Set(), c = /* @__PURE__ */ new Set(), l = /* @__PURE__ */ new Set(), d = /* @__PURE__ */ new Set();
	if (i) return e.model.messages.forEach(({ id: e }) => s.add(e)), e.model.events?.forEach(({ id: e }) => l.add(e)), e.model.participants.forEach(({ id: e }) => d.add(e)), Object.freeze({
		index: r,
		messageCount: a,
		kind: "overview",
		visibleMessageIds: s,
		pastMessageIds: c,
		visibleEventIds: l,
		revealedParticipantIds: d,
		cumulativeBounds: o,
		currentStepBounds: o,
		fullBounds: o
	});
	for (let t = 0; t <= r; t += 1) {
		let n = e.model.messages[t];
		n && (s.add(n.id), d.add(n.from), d.add(n.to), t < r && c.add(n.id));
	}
	let f = new Map((e.model.events ?? []).map((e) => [e.id, e]));
	for (let e of t.content?.values() ?? []) if (e.reveal.fromMessage !== null && e.reveal.fromMessage <= r) {
		l.add(e.eventId);
		for (let t of f.get(e.eventId)?.participants ?? []) d.add(t);
	}
	let m = [], h = [];
	for (let n = 0; n <= r; n += 1) {
		let i = e.model.messages[n], a = i ? t.messages.get(i.id)?.elements ?? [] : [];
		m.push(...a), n === r && h.push(...a);
	}
	let g = /* @__PURE__ */ new Set([
		"activation",
		"fragment-opening",
		"fragment-branch",
		"rect-background"
	]);
	for (let e of t.content?.values() ?? []) l.has(e.eventId) && !g.has(e.role) && (m.push(...e.elements), e.reveal.fromMessage === r && h.push(...e.elements));
	let _ = u(p(m, n));
	if (!_) return;
	let v = _.y + _.height + 8, y = {
		x: o.x,
		y: o.y,
		width: o.width,
		height: Math.max(0, v - o.y)
	}, b = (e) => [...t.content?.values() ?? []].flatMap((t) => !l.has(t.eventId) || e && t.reveal.fromMessage !== r ? [] : p(t.elements, n, g.has(t.role) && t.reveal.toMessage !== null && t.reveal.toMessage > r ? y : void 0)), x = (i) => e.model.messages.flatMap((e, a) => a <= r && (!i || a === r) ? p(t.messages.get(e.id)?.elements ?? [], n) : []), S = [...d].flatMap((e) => p(t.participants.get(e)?.header ?? [], n)), C = [...d].flatMap((e) => p(t.participants.get(e)?.lifeline ?? [], n, y)), w = u([
		...x(!1),
		...b(!1),
		...S,
		...C
	]), T = u([...x(!0), ...b(!0)]);
	if (w && T) return Object.freeze({
		index: r,
		messageCount: a,
		kind: "message",
		currentMessageId: e.model.messages[r].id,
		visibleMessageIds: s,
		pastMessageIds: c,
		visibleEventIds: l,
		revealedParticipantIds: d,
		frontier: v,
		cumulativeBounds: w,
		currentStepBounds: T,
		fullBounds: o
	});
}
//#endregion
//#region src/relationships/traversal.ts
var h = () => ({
	ancestors: /* @__PURE__ */ new Set(),
	current: /* @__PURE__ */ new Set(),
	descendants: /* @__PURE__ */ new Set(),
	both: /* @__PURE__ */ new Set(),
	edges: /* @__PURE__ */ new Set()
});
function g(e) {
	let t = new Set(e.nodes.map(({ id: e }) => e)), n = /* @__PURE__ */ new Map(), r = /* @__PURE__ */ new Map();
	for (let i of e.edges) i.visible && t.has(i.start) && t.has(i.end) && ((r.get(i.start) ?? r.set(i.start, []).get(i.start))?.push(i), (n.get(i.end) ?? n.set(i.end, []).get(i.end))?.push(i));
	let i = (e, t, n) => {
		let r = /* @__PURE__ */ new Set(), i = /* @__PURE__ */ new Set(), a = [e];
		for (; a.length;) {
			let e = a.pop();
			if (e !== void 0) for (let o of t.get(e) ?? []) {
				i.add(o.id);
				let e = n(o);
				r.has(e) || (r.add(e), a.push(e));
			}
		}
		return r.delete(e), {
			nodes: r,
			edges: i
		};
	};
	return { trace(e) {
		if (!t.has(e)) return h();
		let a = i(e, n, (e) => e.start), o = i(e, r, (e) => e.end), s = new Set([...a.nodes].filter((e) => o.nodes.has(e)));
		return {
			ancestors: a.nodes,
			current: /* @__PURE__ */ new Set([e]),
			descendants: o.nodes,
			both: s,
			edges: /* @__PURE__ */ new Set([...a.edges, ...o.edges])
		};
	} };
}
//#endregion
//#region src/relationships/highlight.ts
var _ = "http://www.w3.org/2000/svg", v = ".mermaiden-relationship-visual,.mermaiden-relationship-interaction";
function y(e) {
	for (let t of e.querySelectorAll(v)) t.remove();
	e.parentElement?.classList.remove("relationships-active");
}
function b(e, t) {
	let n = /* @__PURE__ */ new Map(), r = /* @__PURE__ */ new Set();
	for (let i of e) {
		let e = t(i);
		n.has(e) ? (n.delete(e), r.add(e)) : r.has(e) || n.set(e, i);
	}
	return n;
}
function x(e) {
	let t = b(e.model.nodes, ({ id: e }) => e), n = b(e.rendered.nodes, ({ nodeId: e }) => e), r = b(e.rendered.nodes, ({ elementId: e }) => e), i = /* @__PURE__ */ new Map(), a = [...t.values()].flatMap((e) => {
		let t = n.get(e.id);
		return !t || r.get(t.elementId) !== t ? [] : (i.set(e.id, t.elementId), [{
			id: e.id,
			label: e.label
		}]);
	}), o = new Set(a.map(({ id: e }) => e)), s = b(e.model.edges, ({ id: e }) => e), c = b(e.rendered.edges, ({ edgeId: e }) => e), l = b(e.rendered.edges, ({ dataId: e }) => e), u = /* @__PURE__ */ new Map();
	return {
		model: {
			nodes: a,
			edges: [...s.values()].flatMap((e) => {
				let t = c.get(e.id);
				return !o.has(e.start) || !o.has(e.end) || !t || l.get(t.dataId) !== t ? [] : (u.set(e.id, t.dataId), [e]);
			})
		},
		nodeElementIds: i,
		edgeDataIds: u
	};
}
function S(e, t) {
	let n = null;
	try {
		n = typeof t.getScreenCTM == "function" ? t.getScreenCTM() : null;
	} catch {
		n = null;
	}
	let r = n ? Math.hypot(n.a, n.b) : 1, i = n ? Math.hypot(n.c, n.d) : 1, a = 48 / (r > 0 ? r : 1), o = 48 / (i > 0 ? i : 1), s = Math.max(e.width, a), c = Math.max(e.height, o);
	return {
		x: e.x - (s - e.width) / 2,
		y: e.y - (c - e.height) / 2,
		width: s,
		height: c
	};
}
function C(e, t) {
	try {
		let n = e.getBBox(), r = typeof e.getScreenCTM == "function" ? e.getScreenCTM() : null, i = typeof t.getScreenCTM == "function" ? t.getScreenCTM() : null;
		if (r && i && typeof t.createSVGPoint == "function") {
			let e = i.inverse(), a = [
				[n.x, n.y],
				[n.x + n.width, n.y],
				[n.x, n.y + n.height],
				[n.x + n.width, n.y + n.height]
			].map(([n, i]) => {
				let a = t.createSVGPoint();
				return a.x = n ?? 0, a.y = i ?? 0, a.matrixTransform(r).matrixTransform(e);
			}), o = a.map(({ x: e }) => e), s = a.map(({ y: e }) => e), c = {
				x: Math.min(...o),
				y: Math.min(...s),
				width: Math.max(...o) - Math.min(...o),
				height: Math.max(...s) - Math.min(...s)
			};
			return Object.values(c).every(Number.isFinite) && c.width > 0 && c.height > 0 ? c : void 0;
		}
		let a = e.getCTM();
		if (!a || typeof t.createSVGPoint != "function") return [
			n.x,
			n.y,
			n.width,
			n.height
		].every(Number.isFinite) && n.width > 0 && n.height > 0 ? n : void 0;
		let o = [
			[n.x, n.y],
			[n.x + n.width, n.y],
			[n.x, n.y + n.height],
			[n.x + n.width, n.y + n.height]
		].map(([e, n]) => {
			let r = t.createSVGPoint();
			return r.x = e ?? 0, r.y = n ?? 0, r.matrixTransform(a);
		}), s = o.map(({ x: e }) => e), c = o.map(({ y: e }) => e), l = {
			x: Math.min(...s),
			y: Math.min(...c),
			width: Math.max(...s) - Math.min(...s),
			height: Math.max(...c) - Math.min(...c)
		};
		return Object.values(l).every(Number.isFinite) && l.width > 0 && l.height > 0 ? l : void 0;
	} catch {
		return;
	}
}
function w(e, t, n) {
	n?.signal?.throwIfAborted();
	let r = e.ownerDocument, i = (e) => r.createElementNS(_, e), a = n?.canonicalSvg ?? e, o = i("g");
	o.classList.add("mermaiden-relationship-visual"), o.setAttribute("aria-hidden", "true");
	let s = i("g");
	s.classList.add("mermaiden-relationship-interaction"), s.setAttribute("role", "group"), s.setAttribute("aria-label", "Diagram relationship navigation");
	let c = /* @__PURE__ */ new Map(), l = [], u = /* @__PURE__ */ new Map(), d = /* @__PURE__ */ new Map(), f = b([...a.querySelectorAll("[id]")], ({ id: e }) => e), p = b([...a.querySelectorAll("path[data-id]")], (e) => e.getAttribute("data-id") ?? ""), m = t.nodes.flatMap((e) => {
		let t = f.get(n.nodeElementIds.get(e.id) ?? "");
		return t ? [{
			node: e,
			canonical: t
		}] : [];
	}), h = new Set(m.map(({ node: e }) => e.id)), v = [];
	for (let e of t.edges.filter(({ visible: e }) => e)) {
		if (!h.has(e.start) || !h.has(e.end)) continue;
		let t = p.get(n.edgeDataIds.get(e.id) ?? ""), r = t?.getAttribute("d");
		if (!t || !r) continue;
		let i = t.getAttribute("transform") ?? void 0;
		d.set(e.id, Object.freeze({
			d: r,
			...i ? { transform: i } : {}
		})), v.push(e);
	}
	let y = {
		nodes: m.map(({ node: e }) => e),
		edges: v
	}, x = g(y), w = /* @__PURE__ */ new Map();
	for (let e of y.nodes) w.set(e.label, (w.get(e.label) ?? 0) + 1);
	for (let { node: t, canonical: r } of m) {
		let a = n?.nodeSurfaces?.get(t.id), o = C(a || r, e);
		if (!o) continue;
		c.set(t.id, Object.freeze({ ...o }));
		let d = i("rect");
		for (let [t, n] of Object.entries(S(o, e))) d.setAttribute(t, String(n));
		d.classList.add("relationship-hit-target"), d.setAttribute("data-relationship-node", t.id);
		let f = w.get(t.label) === 1 ? t.label : `${t.label} (${t.id})`;
		d.setAttribute("role", "button"), d.setAttribute("aria-label", `${f}: show related nodes`), d.setAttribute("tabindex", l.length === 0 ? "0" : "-1"), s.append(d), l.push(d), u.set(d, t.id);
	}
	if (l.length === 0) return;
	e.append(o, s);
	let T, E = () => {
		T?.classList.remove("relationships-active"), T = void 0, o.replaceChildren();
	}, D = (t) => {
		E(), T = e.parentElement ?? void 0, T?.classList.add("relationships-active");
		let n = x.trace(t), r = [];
		for (let [e, t] of c) {
			let a = n.current.has(e) ? "current" : n.both.has(e) ? "both" : n.ancestors.has(e) ? "ancestor" : n.descendants.has(e) ? "descendant" : void 0;
			if (!a) continue;
			let o = i("rect");
			for (let [e, n] of Object.entries(t)) o.setAttribute(e, String(n));
			o.setAttribute("rx", "8"), o.setAttribute("data-relationship-node", e), o.classList.add("relationship-node-overlay", `relationship-node--${a}`), r.push(o);
		}
		for (let e of n.edges) {
			let t = d.get(e);
			if (!t) continue;
			let n = i("path");
			n.setAttribute("d", t.d), t.transform && n.setAttribute("transform", t.transform), n.classList.add("relationship-edge-overlay", "relationship-edge--active"), r.push(n);
		}
		o.replaceChildren(...r);
	}, O = [], k = (e, t) => {
		s.addEventListener(e, t), n?.onListenerCountChange?.(1), O.push(() => {
			s.removeEventListener(e, t), n?.onListenerCountChange?.(-1);
		});
	}, A = (e) => {
		let t = e.target instanceof Element ? e.target.closest(".relationship-hit-target") : null;
		return t && s.contains(t) ? t : void 0;
	}, j = (e) => {
		let t = e.relatedTarget instanceof Element ? e.relatedTarget.closest(".relationship-hit-target") : null;
		return t && s.contains(t) ? t : void 0;
	};
	k("pointerover", (e) => {
		let t = A(e);
		t && j(e) !== t && D(u.get(t) ?? "");
	}), k("pointerout", (e) => {
		let t = A(e);
		t && j(e) !== t && r.activeElement !== t && E();
	}), k("focusin", (e) => {
		let t = A(e);
		t && (l.forEach((e) => e.setAttribute("tabindex", e === t ? "0" : "-1")), D(u.get(t) ?? ""));
	}), k("focusout", (e) => {
		(!(e.relatedTarget instanceof Node) || !s.contains(e.relatedTarget)) && E();
	}), k("keydown", (e) => {
		let t = A(e);
		if (!t) return;
		if (e.key === "Escape") {
			e.preventDefault(), E();
			return;
		}
		let n = e.key === "Home" ? 0 : e.key === "End" ? l.length - 1 : void 0, r = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
		if (r === 0 && n === void 0) return;
		e.preventDefault();
		let i = l.indexOf(t), a = n ?? (i + r + l.length) % l.length;
		l.forEach((e, t) => e.setAttribute("tabindex", t === a ? "0" : "-1")), l[a]?.focus();
	});
	let M = !1, N = { dispose() {
		if (!M) {
			M = !0, E();
			for (let e of O) e();
			o.remove(), s.remove();
		}
	} };
	return n?.signal?.aborted && (N.dispose(), n.signal.throwIfAborted()), N;
}
function T(e, t, n = {}) {
	let r = x(t);
	return w(e, r.model, {
		...n,
		nodeElementIds: r.nodeElementIds,
		edgeDataIds: r.edgeDataIds
	});
}
//#endregion
//#region src/sequence/focus.ts
var E = "data-mermaiden-sequence-tabindex-baseline", D = "data-mermaiden-sequence-focus-owners";
function O(e) {
	return new Set((e.getAttribute(D) ?? "").split(" ").filter(Boolean));
}
function k(e, t) {
	let n = O(e);
	n.size === 0 && e.setAttribute(E, e.getAttribute("tabindex") ?? "__missing__"), n.add(t), e.setAttribute(D, [...n].join(" ")), e.setAttribute("tabindex", "-1");
}
function A(e, t) {
	let n = O(e);
	if (n.delete(t), n.size > 0) {
		e.setAttribute(D, [...n].join(" ")), e.setAttribute("tabindex", "-1");
		return;
	}
	let r = e.getAttribute(E);
	r === "__missing__" ? e.removeAttribute("tabindex") : r !== null && e.setAttribute("tabindex", r), e.removeAttribute(E), e.removeAttribute(D);
}
//#endregion
//#region src/sequence/svgReferences.ts
var j = /url\(\s*(?:"(#[^"]+)"|'(#[^']+)'|(#[^\s)]+))\s*\)/g, M = /* @__PURE__ */ new Set(["aria-labelledby", "aria-describedby"]);
function N(e, t, n, r) {
	return e === "href" || e === "xlink:href" ? t.replace(/^(\s*)#([^\s]+)(\s*)$/, (e, t, i, a) => {
		r?.(i);
		let o = n.get(i);
		return o ? `${t}#${o}${a}` : e;
	}) : M.has(e) ? t.replace(/\S+/g, (e) => (r?.(e), n.get(e) ?? e)) : t.replace(j, (e, t, i, a) => {
		let o = t ?? i ?? a, s = o?.startsWith("#") ? o.slice(1) : void 0;
		s && r?.(s);
		let c = s ? n.get(s) : void 0;
		return c && o ? e.replace(o, `#${c}`) : e;
	});
}
function P(e) {
	let t = /* @__PURE__ */ new Set();
	for (let n of [e, ...e.querySelectorAll("*")]) for (let e of n.attributes) N(e.name, e.value, /* @__PURE__ */ new Map(), (e) => t.add(e));
	return t;
}
function F(e, t) {
	let n = e.cloneNode(!0);
	for (let e of [n, ...n.querySelectorAll("*")]) for (let n of [...e.attributes]) {
		let r = N(n.name, n.value, t);
		r !== n.value && e.setAttribute(n.name, r);
	}
	for (let e of [n, ...n.querySelectorAll("[id]")]) {
		let n = t.get(e.id);
		n && (e.id = n);
	}
	return n;
}
function I(e, t) {
	let n = /* @__PURE__ */ new Map(), r = /* @__PURE__ */ new Set();
	for (let t of e.querySelectorAll("[id]")) n.has(t.id) ? (n.delete(t.id), r.add(t.id)) : r.has(t.id) || n.set(t.id, t);
	let i = new Set(t.flatMap((e) => [e, ...e.querySelectorAll("[id]")].map((e) => e.id).filter(Boolean))), a = [], o = /* @__PURE__ */ new Set(), s = t.flatMap((e) => [...P(e)]);
	for (; s.length > 0;) {
		let e = s.pop();
		if (!e || o.has(e) || i.has(e)) continue;
		o.add(e);
		let t = n.get(e);
		if (t) {
			a.push(t);
			for (let e of P(t)) o.has(e) || s.push(e);
		}
	}
	return a;
}
//#endregion
//#region src/sequence/playback.ts
var L = "data-mermaiden-sequence-playback", R = "data-mermaiden-sequence-state", z = "data-mermaiden-sequence-marker", B = "data-mermaiden-sequence-clip-wrapper", V = "http://www.w3.org/2000/svg", H = 0, U = (e) => `${z}-${e.slice(7)}`;
function W(e, t) {
	let n = e.model.messages.length, r = n === 0 || t === n, i = /* @__PURE__ */ new Set();
	return r ? e.model.participants.forEach(({ id: e }) => i.add(e)) : e.model.messages.slice(0, t + 1).forEach(({ from: e, to: t }) => {
		i.add(e), i.add(t);
	}), Object.freeze({
		index: r && n === 0 ? 0 : t,
		messageCount: n,
		kind: r ? "overview" : "message",
		revealedParticipantIds: i
	});
}
function G(e, t) {
	e.onUnavailable?.(t);
}
function K(e, t) {
	if (!t.svg.isConnected) return !1;
	let n = new Set(e.model.participants.map(({ id: e }) => e));
	if (n.size !== e.model.participants.length) return !1;
	let r = /* @__PURE__ */ new Set();
	for (let i of e.model.messages) {
		if (r.has(i.id) || !n.has(i.from) || !n.has(i.to) || !t.messages.has(i.id)) return !1;
		r.add(i.id);
	}
	return [...new Set(e.model.messages.flatMap(({ from: e, to: t }) => [e, t]))].every((e) => t.participants.has(e)) && [...t.participants.values()].every((e) => [
		...e.header,
		...e.footer,
		...e.lifeline
	].every((e) => t.svg.contains(e))) && [...t.messages.values()].every((e) => e.elements.every((e) => t.svg.contains(e))) && [...t.content?.values() ?? []].every((e) => e.elements.every((e) => t.svg.contains(e)));
}
function q(e) {
	return [e, ...e.querySelectorAll("a,button,[tabindex]")];
}
function J(e) {
	for (let t of [...e.querySelectorAll(`g[${B}]`)]) {
		let e = t.parentNode;
		if (e) for (; t.firstChild;) e.insertBefore(t.firstChild, t);
		t.remove();
	}
	for (let t of e.querySelectorAll(`[${L}]`)) t.remove();
	e.removeAttribute(L);
	for (let t of e.querySelectorAll("*")) for (let e of [...t.attributes]) e.name.startsWith(`${z}-`) && t.removeAttribute(e.name);
	for (let t of e.querySelectorAll("[data-mermaiden-sequence-content-role]")) {
		let e = t.getAttribute("data-mermaiden-playback-prior-content-role");
		e === "__missing__" ? t.removeAttribute("data-mermaiden-sequence-content-role") : e !== null && t.setAttribute("data-mermaiden-sequence-content-role", e), t.removeAttribute("data-mermaiden-playback-prior-content-role");
	}
	for (let t of [e, ...e.querySelectorAll(`[${R}]`)].filter((e) => e.hasAttribute(R))) {
		let e = t.getAttribute("data-mermaiden-playback-prior-state");
		e === "__missing__" ? t.removeAttribute(R) : e !== null && t.setAttribute(R, e);
		for (let e of [
			"sequence-playback-message",
			"sequence-playback-participant",
			"sequence-playback-content"
		]) t.getAttribute(`data-mermaiden-playback-had-${e}`) !== "true" && t.classList.remove(e);
		t.removeAttribute("data-mermaiden-playback-prior-state"), t.removeAttribute("data-mermaiden-playback-had-sequence-playback-message"), t.removeAttribute("data-mermaiden-playback-had-sequence-playback-participant"), t.removeAttribute("data-mermaiden-playback-had-sequence-playback-content");
		for (let e of q(t)) {
			let t = e.getAttribute("data-mermaiden-playback-aria-hidden");
			A(e, "playback"), t === "__missing__" ? e.removeAttribute("aria-hidden") : t !== null && e.setAttribute("aria-hidden", t), e.removeAttribute("data-mermaiden-playback-aria-hidden");
		}
	}
}
function ee(e, t, n = {}) {
	if (n.signal?.aborted) return G(n, "Sequence playback was aborted.");
	if (e.hasAttribute(L) || e.querySelector(`[${L}]`)) return G(n, "Sequence playback is already attached.");
	let r = n.resolved ?? a(e, t);
	if (!r || r.svg !== e) return G(n, "Sequence element references do not resolve on this SVG.");
	if (!K(t, r)) return G(n, "Sequence playback requires complete message and endpoint correspondence.");
	let i = n.measure ?? c, o = /* @__PURE__ */ new Map(), s = /* @__PURE__ */ new Set();
	for (let e of r.participants.values()) for (let t of [
		...e.header,
		...e.footer,
		...e.lifeline
	]) s.add(t);
	for (let e of r.messages.values()) for (let t of e.elements) s.add(t);
	for (let e of r.content?.values() ?? []) for (let t of e.elements) s.add(t);
	for (let t of s) {
		let r = i(t, e);
		if (!r || !l(r, !0)) return G(n, "Sequence geometry could not be measured.");
		o.set(t, r);
	}
	let u = i(e, e);
	u && l(u) && o.set(e, u);
	let f = /* @__PURE__ */ new Map(), p = /* @__PURE__ */ new Set();
	for (let t of e.querySelectorAll("marker[id]")) f.has(t.id) ? (f.delete(t.id), p.add(t.id)) : p.has(t.id) || f.set(t.id, t);
	let h = [], g = ++H;
	for (let [e, n] of t.model.messages.entries()) for (let t of r.messages.get(n.id)?.elements ?? []) for (let n of [t, ...t.querySelectorAll("[marker-start],[marker-mid],[marker-end]")]) for (let t of [
		"marker-start",
		"marker-mid",
		"marker-end"
	]) {
		let r = /^url\(\s*["']?#([^)'"\s]+)["']?\s*\)$/.exec(n.getAttribute(t) ?? ""), i = r?.[1] ? f.get(r[1]) : void 0;
		i && h.push({
			target: n,
			property: t,
			source: i,
			token: `${g}-${e}-${h.length}`
		});
	}
	if (h.some(({ target: e, property: t }) => e.hasAttribute(U(t)))) return G(n, "Sequence marker treatment is already owned by another attachment.");
	if (e.setAttribute(L, ""), h.length > 0) {
		let t = e.ownerDocument.createElementNS(V, "defs"), n = e.ownerDocument.createElementNS(V, "style");
		t.setAttribute(L, ""), n.setAttribute(L, "");
		let r = [];
		for (let { target: n, property: i, source: a, token: o } of h) {
			let s = `mermaiden-playback-marker-${o}`, c = /* @__PURE__ */ new Map(), l = 0;
			for (let e of [a, ...a.querySelectorAll("[id]")]) e.id && c.set(e.id, e === a ? s : `${s}-${l++}-${e.id.replace(/[^a-zA-Z0-9_-]/g, "-")}`);
			let u = I(e, [a]), d = 0;
			for (let e of u) for (let t of [e, ...e.querySelectorAll("[id]")]) t.id && !c.has(t.id) && c.set(t.id, `${s}-definition-${d++}-${t.id.replace(/[^a-zA-Z0-9_-]/g, "-")}`);
			let f = F(a, c);
			for (let e of u) t.append(F(e, c));
			let p = U(i);
			f.id = s, f.classList.add("mermaiden-sequence-past-marker"), t.append(f), n.setAttribute(p, o), r.push(`[${R}="past"] [${p}="${o}"],[${R}="past"][${p}="${o}"]{${i}:url(#${s})!important}`);
		}
		n.textContent = `${r.join("\n")}\n.mermaiden-sequence-past-marker{filter:grayscale(1) contrast(.62)}`, e.append(t, n);
	}
	let _ = /* @__PURE__ */ new Map();
	for (let t of r.content?.values() ?? []) {
		if (![
			"activation",
			"fragment-opening",
			"fragment-branch",
			"rect-background"
		].includes(t.role)) continue;
		let n = t.elements.filter((e) => !t.elements.some((t) => t !== e && t.contains(e))), r = [];
		for (let i of n) {
			let n = o.get(i), a = i.parentNode;
			if (!n || !a) continue;
			let s = e.ownerDocument.createElementNS(V, "g");
			s.setAttribute(B, ""), s.setAttribute("data-mermaiden-sequence-content-event", t.eventId), a.insertBefore(s, i), s.append(i), r.push({
				wrapper: s,
				bounds: n
			});
		}
		_.set(t.eventId, r);
	}
	let v = /* @__PURE__ */ new Set(), y = (e, t) => {
		e.setAttribute(`data-mermaiden-playback-had-${t}`, String(e.classList.contains(t))), e.setAttribute("data-mermaiden-playback-prior-state", e.getAttribute(R) ?? "__missing__"), e.classList.add(t), e.setAttribute(R, "native"), v.add(e);
	};
	for (let e of r.participants.values()) for (let t of [
		...e.header,
		...e.footer,
		...e.lifeline
	]) y(t, "sequence-playback-participant");
	for (let e of r.messages.values()) for (let t of e.elements) y(t, "sequence-playback-message");
	for (let e of r.content?.values() ?? []) for (let t of e.elements) y(t, "sequence-playback-content"), t.setAttribute("data-mermaiden-playback-prior-content-role", t.getAttribute("data-mermaiden-sequence-content-role") ?? "__missing__"), t.setAttribute("data-mermaiden-sequence-content-role", e.role);
	let b = /* @__PURE__ */ new Set(), x = 0, S = t.model.messages.length === 0, C = !1, w, T = (e, t) => {
		for (let n of q(e)) if (t) n.hasAttribute("data-mermaiden-playback-aria-hidden") || n.setAttribute("data-mermaiden-playback-aria-hidden", n.getAttribute("aria-hidden") ?? "__missing__"), k(n, "playback"), n.setAttribute("aria-hidden", "true");
		else {
			let e = n.getAttribute("data-mermaiden-playback-aria-hidden");
			A(n, "playback"), e === "__missing__" ? n.removeAttribute("aria-hidden") : e !== null && n.setAttribute("aria-hidden", e), n.removeAttribute("data-mermaiden-playback-aria-hidden");
		}
	}, E = (e) => {
		let i = m(t, r, o, x, S);
		if (!i) return;
		w = i, t.model.messages.forEach((e, t) => {
			let n = i.kind === "overview" || t === x ? "native" : i.pastMessageIds.has(e.id) ? "past" : "hidden";
			for (let t of r.messages.get(e.id)?.elements ?? []) t.setAttribute(R, n), T(t, n === "hidden");
		});
		for (let e of t.model.participants) {
			let t = !i.revealedParticipantIds.has(e.id), n = r.participants.get(e.id);
			if (n) {
				for (let e of [...n.header, ...n.lifeline]) e.setAttribute(R, t ? "hidden" : "native"), T(e, t);
				for (let e of n.footer) {
					let n = i.kind !== "overview" || t;
					e.setAttribute(R, n ? "hidden" : "native"), T(e, n);
				}
			}
		}
		for (let e of r.content?.values() ?? []) {
			let t = i.kind !== "overview" && !i.visibleEventIds.has(e.eventId);
			for (let n of e.elements) n.setAttribute(R, t ? "hidden" : "native"), T(n, t);
			for (let { wrapper: t, bounds: n } of _.get(e.eventId) ?? []) {
				let r = i.kind === "message" && i.frontier !== void 0 && e.reveal.toMessage !== null && e.reveal.toMessage > x && n.height > 0 ? Math.max(0, Math.min(100, (n.y + n.height - i.frontier) / n.height * 100)) : 0;
				t.style.setProperty("clip-path", r > 0 ? `inset(0 0 ${r}% 0)` : "none");
			}
		}
		let a = d(i.kind === "overview" ? i.fullBounds : i.cumulativeBounds, n.padding ?? 16), s = d(i.cumulativeBounds, n.padding ?? 16), c = d(i.currentStepBounds, n.padding ?? 16), l = d(i.fullBounds, n.padding ?? 16);
		if (a && s && c && l && n.onFitRequest?.({
			kind: i.kind,
			bounds: a,
			cumulativeBounds: s,
			currentStepBounds: c,
			fullBounds: l
		}), e) for (let e of b) e(i);
	}, D = (e) => {
		if (C || !Number.isFinite(e) || !Number.isInteger(e)) return;
		let n = t.model.messages.length;
		if (e === n) {
			O(!0);
			return;
		}
		if (n === 0) return;
		let r = Math.max(0, Math.min(n - 1, e));
		(r !== x || S) && (x = r, S = !1, E(!0));
	}, O = (e) => {
		C || t.model.messages.length === 0 && !e || S === e || (S = e, E(!0));
	}, j = {
		getState: () => w,
		setIndex: D,
		setOverview: O,
		next: () => {
			!S && x < t.model.messages.length - 1 && D(x + 1);
		},
		previous: () => {
			S || D(x - 1);
		},
		subscribe(e) {
			return C ? () => {} : (b.add(e), () => b.delete(e));
		},
		dispose() {
			C || (C = !0, b.clear(), J(e), n.signal?.removeEventListener("abort", M));
		}
	}, M = () => j.dispose();
	return n.signal?.addEventListener("abort", M, { once: !0 }), n.signal?.aborted ? (j.dispose(), G(n, "Sequence playback was aborted.")) : (E(!1), j);
}
//#endregion
//#region src/sequence/pinnedRows.ts
var Y = "mermaiden-sequence-pinned-layer", X = "data-mermaiden-sequence-pinned-native", Z = "http://www.w3.org/2000/svg", te = 0;
function Q(e, t) {
	e.onUnavailable?.(t);
}
function $(e) {
	return e.replace(/[^a-zA-Z0-9_-]/g, "-");
}
function ne(e, t, n) {
	let r = I(e, t), i = /* @__PURE__ */ new Map(), a = 0;
	for (let e of r) for (let t of [e, ...e.querySelectorAll("[id]")]) {
		let e = t.getAttribute("id");
		e && !i.has(e) && i.set(e, `${n}-definition-${a++}-${$(e)}`);
	}
	return {
		rows: t.map((e, t) => {
			let r = new Map(i), a = 0;
			for (let i of [e, ...e.querySelectorAll("[id]")]) {
				let e = i.getAttribute("id");
				e && r.set(e, `${n}-row-${t}-${a++}-${$(e)}`);
			}
			return F(e, r);
		}),
		definitions: r.map((e) => F(e, i))
	};
}
function re(e) {
	e.previousElementSibling?.matches(`svg.${Y}.mermaiden-sequence-frozen-underlay`) && e.previousElementSibling.remove();
	for (let t of e.querySelectorAll(`.${Y}`)) t.remove();
	for (let t of [e, ...e.querySelectorAll(`[${X}]`)].filter((e) => e.hasAttribute(X))) {
		t.getAttribute("data-mermaiden-pinned-had-class") !== "true" && t.classList.remove("sequence-pinned-native");
		for (let e of [t, ...t.querySelectorAll("a,button,[tabindex]")]) A(e, "pinned");
		t.removeAttribute("data-mermaiden-pinned-had-class"), t.removeAttribute(X);
	}
}
function ie(e, t, n) {
	if (n.signal?.aborted) return Q(n, "Frozen sequence headers were aborted.");
	if (n.overlay.querySelector(`.${Y}`)) return Q(n, "Frozen sequence headers are already attached.");
	let r = n.resolved ?? a(e, t);
	if (!r || r.svg !== e) return Q(n, "Sequence element references do not resolve on this SVG.");
	if (!e.isConnected || [...r.participants.values()].some((t) => [
		...t.header,
		...t.footer,
		...t.lifeline
	].some((t) => !e.contains(t)))) return Q(n, "Resolved sequence rows belong to another or detached SVG.");
	let i = (e) => new Set([...e].filter((e) => r.participants.get(e)?.header.length)), o = i(new Set(n.visibleParticipantIds ?? r.participants.keys())), s = n.measure ?? c, d = Math.max(0, n.rowPadding ?? 4), f = /* @__PURE__ */ new Map(), p = () => {
		f.clear();
		for (let t of r.participants.values()) for (let n of [
			...t.header,
			...t.footer,
			...t.lifeline
		]) {
			let t = s(n, e);
			if (!t || !l(t, !0)) return !1;
			f.set(n, t);
		}
		return !0;
	};
	if (!p()) return Q(n, "Frozen participant header geometry could not be measured.");
	let m = n.viewport.getMatrix(), h = n.viewport.getSize();
	if (![
		m.a,
		m.b,
		m.c,
		m.d,
		m.e,
		m.f,
		h.width,
		h.height
	].every(Number.isFinite) || h.width <= 0 || h.height <= 0) return Q(n, "Frozen participant viewport is invalid.");
	if (!(m.a > 0) || m.a !== m.d || m.b !== 0 || m.c !== 0) return Q(n, "Frozen headers require an unrotated uniform viewport.");
	let g = n.overlay.ownerDocument.createElementNS(Z, "g");
	g.classList.add(Y), g.setAttribute("aria-hidden", "true"), g.setAttribute("pointer-events", "none");
	let _ = e.ownerDocument.createElementNS(Z, "svg");
	_.classList.add(Y, "mermaiden-sequence-frozen-underlay"), _.setAttribute("aria-hidden", "true"), _.setAttribute("pointer-events", "none"), _.style.pointerEvents = "none";
	let v = ++te, y = n.overlay.ownerDocument.createElementNS(Z, "defs"), b = n.overlay.ownerDocument.createElementNS(Z, "svg");
	b.setAttribute("x", "0"), b.setAttribute("y", "0"), b.setAttribute("overflow", "hidden");
	let x = n.overlay.ownerDocument.createElementNS(Z, "svg");
	x.setAttribute("x", "0"), x.setAttribute("overflow", "hidden");
	let S = e.ownerDocument.createElementNS(Z, "g");
	S.classList.add("mermaiden-sequence-frozen-lifelines"), _.append(S);
	let C = n.overlay.ownerDocument.createElementNS(Z, "rect");
	C.classList.add("mermaiden-sequence-frozen-background");
	let w = n.overlay.ownerDocument.createElementNS(Z, "rect");
	w.classList.add("mermaiden-sequence-frozen-background");
	let T = n.overlay.ownerDocument.createElementNS(Z, "g");
	T.classList.add("mermaiden-sequence-frozen-connectors");
	let E = n.overlay.ownerDocument.createElementNS(Z, "g");
	E.classList.add("mermaiden-sequence-frozen-connectors");
	let D = n.overlay.ownerDocument.createElementNS(Z, "path");
	D.classList.add("mermaiden-sequence-frozen-separator");
	let O = n.overlay.ownerDocument.createElementNS(Z, "path");
	O.classList.add("mermaiden-sequence-frozen-separator"), g.append(y, C, T, b, D, w, E, x, O), e.parentNode?.insertBefore(_, e), n.overlay.append(g);
	let j = () => {
		for (let e of r.participants.values()) for (let t of [...e.header, ...e.footer]) if (!t.hasAttribute(X)) {
			t.setAttribute("data-mermaiden-pinned-had-class", String(t.classList.contains("sequence-pinned-native"))), t.classList.add("sequence-pinned-native"), t.setAttribute(X, "");
			for (let e of [t, ...t.querySelectorAll("a,button,[tabindex]")]) k(e, "pinned");
		}
	}, M = () => {
		for (let e of r.participants.values()) for (let t of [...e.header, ...e.footer]) if (t.hasAttribute(X)) {
			t.getAttribute("data-mermaiden-pinned-had-class") !== "true" && t.classList.remove("sequence-pinned-native");
			for (let e of [t, ...t.querySelectorAll("a,button,[tabindex]")]) A(e, "pinned");
			t.removeAttribute("data-mermaiden-pinned-had-class"), t.removeAttribute(X);
		}
	}, N = !1, P = !1, F, I = {
		top: 0,
		bottom: 0
	}, L = 0, R = [], z = /* @__PURE__ */ new Map(), B = Number.isFinite(n.bottomOffset) ? Math.max(0, n.bottomOffset ?? 0) : 0, V = (e) => {
		e !== F && (F = e, n.onAvailabilityChange?.(e));
	}, H = () => {
		if (N) return;
		let e = n.viewport.getMatrix(), t = n.viewport.getSize();
		if (![
			e.a,
			e.b,
			e.c,
			e.d,
			e.e,
			e.f,
			t.width,
			t.height
		].every(Number.isFinite) || t.width <= 0 || t.height <= 0) {
			g.setAttribute("visibility", "hidden"), _.setAttribute("visibility", "hidden"), I = {
				top: 0,
				bottom: 0
			}, P &&= (M(), !1), V("Frozen header viewport is unavailable."), n.onUnavailable?.("Frozen header viewport is unavailable.");
			return;
		}
		_.setAttribute("width", String(t.width)), _.setAttribute("height", String(t.height)), b.setAttribute("width", String(t.width)), x.setAttribute("width", String(t.width));
		let r = u(R.filter(({ row: e }) => e === "top").map(({ bounds: e }) => e)), i = u(R.filter(({ row: e }) => e === "bottom").map(({ bounds: e }) => e)), a = r ? r.height * e.d + 2 * d : 0, o = i ? i.height * e.d + 2 * d : 0, s = t.height - B - o, c = e.a > 0 && e.a === e.d && e.b === 0 && e.c === 0, l = !c || Math.max(a, o) > Math.min(120, t.height * .25) || s < a;
		V(l ? c ? "Frozen headers are too large at this zoom. Zoom out to show them." : "Frozen headers require an unrotated uniform viewport." : void 0), g.setAttribute("visibility", l ? "hidden" : "visible"), _.setAttribute("visibility", l ? "hidden" : "visible"), l && P ? (M(), P = !1, n.onUnavailable?.(c ? "Frozen headers are too large at this zoom. Zoom out to show them." : "Frozen headers require an unrotated uniform viewport.")) : !l && !P && (j(), P = !0), I = {
			top: l ? 0 : a,
			bottom: l ? 0 : o
		}, b.setAttribute("height", String(a)), C.setAttribute("width", String(t.width)), C.setAttribute("height", String(a)), D.setAttribute("d", `M0 ${a}H${t.width}`), x.setAttribute("y", String(s)), x.setAttribute("height", String(o)), w.setAttribute("x", "0"), w.setAttribute("y", String(s)), w.setAttribute("width", String(t.width)), w.setAttribute("height", String(Math.max(0, t.height - s))), O.setAttribute("d", `M0 ${s}H${t.width}`);
		for (let t of R) {
			let n = t.row === "top" ? r : i, o = t.row === "top" ? d : d - (n?.y ?? 0) * e.d;
			if (t.wrapper.setAttribute("transform", `matrix(${e.a} 0 0 ${e.d} ${e.e} ${t.row === "top" ? o - (n?.y ?? 0) * e.d : o})`), t.row === "top") {
				let n = z.get(t.element), o = n?.line, c = t.lifeline && f.get(t.lifeline);
				if (o && c && n) {
					let t = (c.x + c.width / 2) * e.a + e.e;
					if (o.setAttribute("x1", String(t)), o.setAttribute("x2", String(t)), o.setAttribute("y1", String(a)), o.setAttribute("y2", String(s)), o.style.setProperty("stroke-width", `${n.strokeWidth * e.a}px`), n.topConnector && r) {
						let i = d + (n.topConnector.bounds.y + n.topConnector.bounds.height - r.y) * e.d;
						n.topConnector.line.setAttribute("x1", String(t)), n.topConnector.line.setAttribute("x2", String(t)), n.topConnector.line.setAttribute("y1", String(i)), n.topConnector.line.setAttribute("y2", String(a)), n.topConnector.line.style.setProperty("stroke-width", `${n.strokeWidth * e.a}px`);
					}
					if (n.bottomConnector && i) {
						let r = s + d + (n.bottomConnector.bounds.y - i.y) * e.d;
						n.bottomConnector.line.setAttribute("x1", String(t)), n.bottomConnector.line.setAttribute("x2", String(t)), n.bottomConnector.line.setAttribute("y1", String(s)), n.bottomConnector.line.setAttribute("y2", String(r)), n.bottomConnector.line.style.setProperty("stroke-width", `${n.strokeWidth * e.a}px`);
					}
				}
			}
		}
	}, U = () => {
		if (N) return;
		let t = [...o].flatMap((e) => {
			let t = r.participants.get(e);
			return (t?.header ?? []).map((e) => ({
				element: e,
				bounds: f.get(e),
				lifeline: t?.lifeline[0]
			}));
		}).filter((e) => !!e.bounds), i = [...o].flatMap((e) => {
			let t = r.participants.get(e);
			return (t?.footer ?? []).map((e) => ({
				element: e,
				bounds: f.get(e),
				lifeline: t?.lifeline[0]
			}));
		}).filter((e) => !!e.bounds), a = [...t.map((e) => ({
			...e,
			row: "top"
		})), ...i.map((e) => ({
			...e,
			row: "bottom"
		}))], s = ne(e, a.map(({ element: e }) => e), `mermaiden-pinned-${v}-${L}`);
		y.replaceChildren(...s.definitions), R = a.flatMap((e, t) => {
			let r = s.rows[t];
			if (!r) return [];
			let i = [e.element, ...e.element.querySelectorAll("*")];
			[r, ...r.querySelectorAll("*")].forEach((e, t) => {
				for (let t of [...e.attributes]) t.name.startsWith("data-mermaiden-") && e.removeAttribute(t.name);
				for (let t of [...e.classList]) (t.startsWith("sequence-playback-") || t.startsWith("sequence-pinned-") || t.startsWith("mermaiden-")) && e.classList.remove(t);
				e.removeAttribute("tabindex"), e.localName === "a" && (e.removeAttribute("href"), e.removeAttribute("xlink:href"));
				let r = i[t], a = r && n.computedStyle?.(r);
				if (a && "style" in e) for (let t of [
					"fill",
					"stroke",
					"stroke-width",
					"font-family",
					"font-size",
					"font-weight",
					"font-style",
					"line-height",
					"text-anchor",
					"dominant-baseline",
					"color",
					"text-align",
					"white-space",
					"opacity",
					"fill-opacity",
					"stroke-opacity"
				]) {
					let n = a.getPropertyValue(t);
					n && !n.includes("url(") && e.style.setProperty(t, n);
				}
			}), r.removeAttribute(X), r.removeAttribute("data-mermaiden-pinned-had-class"), r.classList.remove("sequence-pinned-native");
			for (let e of [r, ...r.querySelectorAll("[data-mermaiden-sequence-focus-owners]")]) e.removeAttribute("data-mermaiden-sequence-tabindex-baseline"), e.removeAttribute("data-mermaiden-sequence-focus-owners"), e.removeAttribute("tabindex");
			let a = n.overlay.ownerDocument.createElementNS(Z, "g");
			r.setAttribute("data-participant-row", e.row);
			let o = n.overlay.ownerDocument.createElementNS(Z, "g"), c = n.parentTransform?.(e.element);
			return c && o.setAttribute("transform", c), o.append(r), a.classList.add("mermaiden-sequence-frozen-row"), a.append(o), [{
				...e,
				clone: r,
				wrapper: a
			}];
		}), b.replaceChildren(...R.filter(({ row: e }) => e === "top").map(({ wrapper: e }) => e)), x.replaceChildren(...R.filter(({ row: e }) => e === "bottom").map(({ wrapper: e }) => e)), z = /* @__PURE__ */ new Map();
		let c = [], l = [], u = (e, t) => {
			e.classList.add("mermaiden-sequence-frozen-lifeline");
			for (let n of [
				"stroke",
				"stroke-width",
				"stroke-opacity",
				"opacity",
				"stroke-linecap"
			]) {
				let r = t?.getPropertyValue(n);
				r && !r.includes("url(") && e.style.setProperty(n, r);
			}
			e.style.setProperty("stroke-dasharray", "none");
		};
		S.replaceChildren(...R.filter(({ row: e, lifeline: t }) => e === "top" && !!t).map((t) => {
			let r = e.ownerDocument.createElementNS(Z, "line"), i = t.lifeline && n.computedStyle?.(t.lifeline);
			u(r, i);
			let a = Number.parseFloat(i?.getPropertyValue("stroke-width") || t.lifeline?.getAttribute("stroke-width") || "1"), o = !t.element.matches(".actor-man"), s = R.find(({ row: e, lifeline: n }) => e === "bottom" && n === t.lifeline), d = o ? {
				line: e.ownerDocument.createElementNS(Z, "line"),
				bounds: t.bounds
			} : void 0, f = o && s && !s.element.matches(".actor-man") ? {
				line: e.ownerDocument.createElementNS(Z, "line"),
				bounds: s.bounds
			} : void 0;
			return d && (u(d.line, i), c.push(d.line)), f && (u(f.line, i), l.push(f.line)), z.set(t.element, {
				line: r,
				topConnector: d,
				bottomConnector: f,
				strokeWidth: Number.isFinite(a) && a >= 0 ? a : 1
			}), r;
		})), T.replaceChildren(...c), E.replaceChildren(...l), L += 1, H();
	}, W = n.viewport.subscribe(H), G = {
		setVisibleParticipantIds(e) {
			if (N) return;
			let t = i(e);
			if (t.size === o.size && [...t].every((e) => o.has(e))) {
				H();
				return;
			}
			o = t, U();
		},
		setBottomOffset(e) {
			if (N) return;
			let t = Number.isFinite(e) ? Math.max(0, e) : 0;
			t !== B && (B = t, H());
		},
		update: H,
		refresh() {
			if (!N) {
				if (!p()) {
					n.onUnavailable?.("Frozen participant header geometry could not be measured.");
					return;
				}
				U();
			}
		},
		getInsets: () => ({ ...I }),
		dispose() {
			N || (N = !0, W(), n.signal?.removeEventListener("abort", K), g.remove(), _.remove(), re(e));
		}
	}, K = () => G.dispose();
	return n.signal?.addEventListener("abort", K, { once: !0 }), n.signal?.aborted ? (G.dispose(), Q(n, "Frozen sequence headers were aborted.")) : (U(), G);
}
//#endregion
export { v as RELATIONSHIP_HIGHLIGHT_LAYER_SELECTOR, T as attachRelationshipHighlight, ie as attachSequencePinnedRows, ee as attachSequencePlayback, W as deriveSequencePlaybackState, m as deriveSequenceProjection, o as intersectSequenceBounds, f as layoutSequenceFit, c as measureSequenceElement, d as padSequenceBounds, a as resolveSequenceElements, n as sequenceDescendantToRootMatrix, y as stripRelationshipHighlight, re as stripSequencePinnedRows, J as stripSequencePlayback, u as unionSequenceBounds, l as validBounds };

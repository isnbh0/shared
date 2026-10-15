# Porter–Duff — Compositing Digital Images (1984)

- **Source:** T. Porter & T. Duff, "Compositing Digital Images," Computer Graphics (SIGGRAPH '84 Proceedings) 18(3), July 1984, pp. 253–259.
- **URL:** https://keithp.com/~keithp/porterduff/p253-porter.pdf
- **Checked:** 2026-10-14 (against the PDF's text layer; the abstract and operator definitions below are verbatim modulo OCR spacing).

## The passages

**Abstract:** "Most computer graphics pictures have been computed all at once, so that the rendering program takes care of all computations relating to the overlap of objects. There are several applications, however, where elements must be rendered separately, relying on compositing techniques for the anti-aliased accumulation of the full image. This paper presents the case for four-channel pictures, demonstrating that a matte component can be computed similarly to the color channels. The paper discusses guidelines for the generation of elements and the arithmetic for their arbitrary compositing."

**On the matte channel:** "Each element has an associated matte, coverage information which designates the shape of the element." The alpha channel treats "an alpha of 0 to indicate no coverage, 1 to mean full coverage, with fractions corresponding to partial coverage."

**On the operators:** "Useful operators include A over B, A in B, and A held out by B. A over B is the placement of foreground A in front of background B." Further: "A held out by B, normally shortened to A out B, refers only to that part of A outside picture B. For completeness, we include the less useful operators A atop B and A xor B. A atop B is the union of A in B and B out A."

## Where it is relied on

[Production lineage](../Production%20lineage.md) uses the paper as the documented origin of compositing as an operation on separately rendered elements. The compositing operations listed in [Operations](../../Operations.md) come from it.

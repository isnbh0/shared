# Karplus–Strong — the algorithm and the decay-stretching patent

- **Sources:**
  - K. Karplus & A. Strong, "Digital Synthesis of Plucked-String and Drum Timbres," Computer Music Journal 7(2), 1983, doi:10.2307/3680062 (not online; cited from secondary sources).
  - A. Strong & K. Karplus, US Patent 4,649,783, "Digital signal processing system for synthesizing sounds" (priority 1983-02-02, granted 1987). https://patents.google.com/patent/US4649783A/en
  - D. A. Jaffe & J. O. Smith, "Extensions of the Karplus-Strong Plucked-String Algorithm," Computer Music Journal 7(2), 1983, doi:10.2307/3680063.
- **Checked:** 2026-10-14 (patent text verified at the Google Patents copy; the CMJ papers are not online).

## The passages

**US Patent 4,649,783, on decay stretching:** "Each of the decay algorithms allows decay stretching during the decay operation with the stretching factor, s, equal to 1, 2, 4, 8, 16, 32, 64, or infinity. The factor s (which equals 1/d) multiplies the unstretched decay time by the value of s." And: "The effect of selecting the PROBd line during the decay operation is to permit probabilistic decay stretching to occur."

**Jaffe & Smith (quoted via Välimäki's thesis):** "Jaffe and Smith (1983) introduced a first-order allpass filter for producing the desired fractional delay." Their extensions also include pick-position comb filtering.

**Source status per the audio source ledger:** partly supported — the decay-stretching claim is sourced to the patent; the original CMJ paper is not online. Only secondary course notes credit the deterministic weighted two-tap loop filter `(1 − S)·y[n−N] + S·y[n−N−1]` to Jaffe & Smith, so that attribution stays open.

## Where it is relied on

[Sound sources and voices](../../knowledge/Sound%20sources%20and%20voices.md) describes SLASH_MY's plucked-string and keys voices as Karplus–Strong. It gives the exact form of the loop filter and notes that the filter's attribution is open. The [Soundtrack code case](../../cases/Soundtrack%20code.md) walks through the voices in full, including the per-pitch loop gain `decay = 10^(−3/(t60·f))`, which no checked source covers.

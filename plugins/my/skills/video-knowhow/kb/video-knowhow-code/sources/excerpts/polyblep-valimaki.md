# PolyBLEP — polynomial band-limited step correction

- **Source:** V. Välimäki & A. Huovilainen, "Antialiasing Oscillators in Subtractive Synthesis," IEEE Signal Processing Magazine 24(2), 2007, doi:10.1109/MSP.2007.323276; and V. Välimäki, J. Pekonen, & V. Nam, "Perceptually informed synthesis of bandlimited classical waveforms," JASA 131(1), 2012, doi:10.1121/1.3651227.
- **URLs:** https://doi.org/10.1109/MSP.2007.323276 · https://doi.org/10.1121/1.3651227
- **Checked:** 2026-10-14 (quote as recorded in the ledger's fetched copy).

## The passage

"a polynomial approximation of the ideal BLEP method, originally proposed by Välimäki and Huovilainen" — the PolyBLEP (polynomial band-limited step) correction replaces the discontinuity of a naive saw or square with a short polynomial residual added over the two samples adjacent to the wrap, removing the aliasing a naive oscillator produces at a fraction of the cost of full band-limited table lookup.

## Where it is relied on

[Sound sources and voices](../../knowledge/Sound%20sources%20and%20voices.md) introduces SLASH_MY's band-limited saw as a PolyBLEP oscillator and states how it works: a two-sample quadratic correction across the wrap. The [Soundtrack code case](../../cases/Soundtrack%20code.md) goes through SLASH_MY's `blep()` implementation line by line and compares it with this method.

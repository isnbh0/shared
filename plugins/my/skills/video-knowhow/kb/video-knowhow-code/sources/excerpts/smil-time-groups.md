# SMIL 1.0 — time containers and the shared clock (1998)

- **Source:** W3C, Synchronized Multimedia Integration Language (SMIL 1.0) Specification, W3C Recommendation 15 June 1998.
- **URL:** https://www.w3.org/TR/1998/REC-smil-19980615/
- **Checked:** 2026-10-14.

## The passages

**Abstract:** "SMIL allows integrating a set of independent multimedia objects into a synchronized multimedia presentation. Using SMIL, an author can 1. describe the temporal behavior of the presentation 2. describe the layout of the presentation on a screen 3. associate hyperlinks with media objects."

**The par element:** "The children of a par element can overlap in time. The textual order of appearance of children in a par has no significance for the timing of their presentation." The body element "implicitly defines a seq element"; in a seq, children play one after another.

**Timing attributes:** `begin` "specifies the time for the explicit begin of an element" (a delay from the parent container's begin, or from the previous sibling's end in a seq); `dur` "specifies the explicit duration of an element"; `end` specifies an explicit end. Presentation time "behaves like the timecode shown on a counter of a tape-deck" — one shared clock for the document, with a synchronization note distinguishing "hard synchronization" (children synchronized "to a common clock") from "soft synchronization" (each child with its own clock).

## Where it is relied on

[Production lineage](../Production%20lineage.md) cites SMIL 1.0 as the documented origin of arranging independent media objects in sequential and parallel time groups with begin times, durations, and a shared clock. The operations "schedule a meaningful event" and "align media to a common time" come from it.

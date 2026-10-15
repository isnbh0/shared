# Temporal visual rhythm

A video spreads events over time: things appear, move, pause, speak, cut, and sound. Rhythm is the pattern of the intervals between those events and of which ones get emphasis. It is more than the number of cuts per minute. Two sequences with the same number of cuts can feel different if one gives each important image a steady hold and the other fills every hold with competing movement.

## Event, hold, and recovery

An **event** changes what the viewer should notice. A **hold** gives a new state time to be understood. A **recovery interval** lets one event settle before another competes with it. These units describe a sequence; a shot does not have to contain all three. A cut can itself be the event, and in another scene the event may be a character's small gesture inside a long shot. How long each unit lasts relative to the others depends on how much information it carries and the feeling you want.

Material Design ties motion duration to the distance traveled and the complexity of the change, so a transition can be understood without needless waiting. Netflix's subtitle guidance times subtitles against speech and cuts, and asks for review in full playback because awkward timing can pass numerical checks. Both are examples, each from its own field, of timing judged against perception and the surrounding events. [Material duration and easing](https://m1.material.io/motion/duration-easing.html), [Netflix subtitle timing guidelines](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines)

## Repetition and variation

When an interval, a motion, a color change, or a shot shape repeats, it lets the viewer learn a pattern, and a later break in that pattern can become emphasis. Repetition can also make every effect feel the same, so how much a strong accent means depends on how often it appears. This is the relative nature of attention (see [Attention and hierarchy](Attention%20and%20hierarchy.md)) applied over time. It does not require a fixed musical grid.

Music offers a time reference in its beats, phrases, drops, and silences, but the picture does not need to change on every beat. Some events can come before or after an accent, and a still image can let the sound carry the change. Code states these relationships through shared timestamps or beat positions. What the viewer perceives still depends on the rendered audio and video; the event table alone does not settle it. [Audiovisual synchronization](../knowledge/Audiovisual%20synchronization.md) covers clocks and implementation.

## What code makes inspectable

An event timeline can record scene boundaries, changes of visual focus, text reading times, audio cues, and intensity. A simple plot of these tracks can show clusters where many things change at once, or long stretches with no clear focal event. The question to ask is whether that density serves the reading and the feeling you intended. Metrics of duration and event count can flag intervals to watch, but they cannot choose the right rhythm on their own. See [Time and motion](../knowledge/Time%20and%20motion.md) and [Transitions and continuity](../knowledge/Transitions%20and%20continuity.md).

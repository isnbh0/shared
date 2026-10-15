# Animated data comparison

**What it makes.** A short chart brings in a small set of values one at a time. The working example compares three labeled values: 34, 89, and 163. The bars rise from one reference baseline, each label stays with its bar, and the largest bar is in a contrasting color. The inputs are checked data, units, labels, a reference baseline that means something for the data, and a decision about which comparison the viewer should look at. The output is a four-second chart segment.

## Design intent

Bar length shows the quantities. With one shared reference baseline the viewer can compare lengths directly, and the highlight color points to one result. Staggered entrances give each bar its own [event](../theory/Attention%20and%20hierarchy.md) to draw the eye before the whole comparison is visible. Once all the bars are up, the chart has to hold still long enough for the viewer to compare them. How long is a question of [temporal visual rhythm](../theory/Temporal%20visual%20rhythm.md); no single animation speed fits every chart. Labels should stay readable at the size the chart is finally shown; see [moving-text legibility](../theory/Moving-text%20legibility.md).

## Operations and techniques

The combination uses these [operations](../Operations.md):

| Pattern | Input and operation | Concrete technique in the working example |
| --- | --- | --- |
| Represent a source; Encode meaning in a visual property | A list of labels and numbers is mapped to bar height and displayed values. | The [Remotion example source](https://www.remotion.dev/elements/data/vertical-bar-chart/) defines three data records, finds the maximum, and scales the bars against it. |
| Relate elements in space; Bind a role to a visual language | Bars share a reference baseline; each value and label stays with its bar; one category receives an accent color. | The example groups each bar with its labels and applies a `highlighted` property to the third value. |
| Schedule a meaningful event; Evaluate a property at a chosen time | Bars grow on staggered frame offsets until they reach the values encoded by their final heights. | The source uses the current video frame, an animation delay based on the record index, and a spring easing function. |
| Sample a specified state | The frame-driven chart is rendered to a video file. | The official page includes [source and an interactive preview](https://www.remotion.dev/elements/data/vertical-bar-chart/); its [published MP4](https://remotion.media/elements/data-vertical-bar-chart-preview.mp4) is the output. |

## What the example proves

The published MP4 is four seconds at 1920 × 1080. I downloaded it and inspected frames from the start, middle, and end: the bars appear in order and finish at 34, 89, and 163. The source on the official page shows how the values set the heights and how the entrances use frame time. The clip has no audio stream and cites no data source. It proves how the animation works and what it renders; any real use still needs verified numbers, units, and context. [Source and preview](https://www.remotion.dev/elements/data/vertical-bar-chart/), [rendered MP4](https://remotion.media/elements/data-vertical-bar-chart-preview.mp4).

## A usable starting configuration

The [official source](https://www.remotion.dev/elements/data/vertical-bar-chart/) is a four-second, 30 fps segment with a small data array of `label`, `value`, and `highlighted`. Change those records and their title or units, then render the composition to MP4. The mapping from data to bar height and the shared reference baseline carry over to SVG, Canvas, or another frame renderer. Pick the highlighted result for what the piece is saying; being the maximum is not reason enough. Before delivery, check the source numbers, the units, what the axis means, the hold on the end state, the label size, and whether a changed value still fits the layout.

For a series that changes over time, the [D3 team's live bar-chart-race example](https://observablehq.com/@d3/bar-chart-race-explained) shows how ranks, bars, labels, axis, and date can update together. It is a browser animation with source you can inspect. It is a separate example and says nothing about whether Remotion's four-second chart can run a race. If the story needs a changing series, keep each bar's identity and the scale relations stable across updates; see [grouping and continuity](../theory/Grouping%20and%20continuity.md).

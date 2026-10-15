# Event announcement opener

**What it makes.** A short video presents an event's talk title, the speaker's portrait and name, the date, the place, and the logo. The inputs are the real event facts, an approved image and logo, a palette, and the output size you plan to deliver. The output is a timed announcement you can render again with different event information.

## Design intent

The viewer should recognize the event, find the talk title, identify the speaker, and then read the practical details. Each of these does a different job, so they need a visible order. [Attention and hierarchy](../theory/Attention%20and%20hierarchy.md) explains how size, isolation, contrast, and entrance timing create that order. [Moving-text legibility](../theory/Moving-text%20legibility.md) adds a second constraint: the title and the details need reading time after they enter. Reusing the same geometry, colors, and type treatment across announcements gives the series a recognizable [visual identity](../theory/Visual%20identity%20and%20style.md).

## Operations and techniques

The combination uses these [operations](../Operations.md):

| Pattern | Input and operation | Concrete technique in the working example |
| --- | --- | --- |
| Represent a source; Expose a decision as a parameter | Title, speaker, photo, logo, date, location, and background color become named inputs. | Shortvid's [talk composition](https://github.com/lyonjs/shortvid.io/blob/main/remotion/compositions/templates/talks/Talk.composition.tsx) registers a 1280 × 720 variant with default values; the branded component receives these values as properties. |
| Bind a role to a visual language; Relate elements in space | The title, portrait, brand, and details keep distinct places and treatments. | The [branded composition](https://github.com/lyonjs/shortvid.io/blob/main/remotion/compositions/templates/talks/talk/branded/TalkBranded.tsx) layers a background, logo, speaker, title, date, and location. |
| Schedule a meaningful event; Evaluate a property at a chosen time | Components enter at different frames, then settle into a readable composition. | The same composition schedules speaker, title, details, and location at frames 10, 40, 50, and 55. The [title](https://github.com/lyonjs/shortvid.io/blob/main/remotion/compositions/templates/talks/talk/branded/BrandedTitle.tsx) varies opacity and blur with frame time. |
| Combine and reveal layers; Sample a specified state | The timed elements become one video image at each frame. | Shortvid publishes an [MP4 example](https://user-images.githubusercontent.com/6263857/214966765-a22cc958-95bb-49fc-9ea9-3a4ef1392fae.mp4) in its [project README](https://github.com/lyonjs/shortvid.io#readme). |

## What the example proves

The project authors publish a five-second, 1280 × 720 MP4. It shows a talk title over branded color fields, then the speaker's portrait and name and the event details. I downloaded the file and checked its video metadata and several frames. The file has no audio stream, so the example shows a silent announcement. The repository holds the source composition and its timed components. The source may have changed since the clip was published, so the clip proves the result and the source shows how the maintained version is built. [Published example](https://github.com/lyonjs/shortvid.io#readme), [composition source](https://github.com/lyonjs/shortvid.io/blob/main/remotion/compositions/templates/talks/talk/branded/TalkBranded.tsx).

## A usable starting configuration

The maintained Shortvid variant is registered at 1280 × 720, 30 fps, and 140 frames, with editable talk title, speakers, images, date, location, logo, and background color. You can [preview and render its components from the repository](https://github.com/lyonjs/shortvid.io). The relations between the elements carry the composition, and a simpler DOM or Canvas build can reuse the same inputs and frame offsets. For a vertical announcement, keep the same roles for each piece of information and measure the portrait, title, and details again against the new frame.

Replace the event facts and assets first, then check the longest real title and the smallest details at the delivery size. Watch the whole clip at normal speed to see whether the reading time is long enough. You can add sound by following [sound and synchronization](../maps/Compose%20sound%20and%20synchronization.md); the published clip does not demonstrate it.

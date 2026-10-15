# Attention and hierarchy in a moving frame

Visual hierarchy is the order in which a viewer is likely to notice and read things. Its signals work by comparison with their surroundings: size, contrast, color, isolation, position, detail, repetition, and movement. Static design treats visual weight as relative and attention as limited. Prominence comes from several signals working together in a composition, so when a hierarchy feels wrong, compare the elements together at the size they will be seen, and give each one visual force in proportion to its role, its urgency, how often the viewer meets it, and how much the task depends on it. IBM likewise describes hierarchy as an entry point and a reading path made from composition, type, and space. [IBM layout guidance](https://www.ibm.com/design/language/layout/tips-and-techniques/) ([excerpt](../sources/excerpts/ibm-layout-reading-path.md))

Video adds **time**. A viewer cannot study a frame for as long as they like. A new motion, a bright change, a cut, or a word reveal can pull the eye away just as an important gesture happens elsewhere in the frame. Motion is a strong signal: in animated graphics it can point viewers to a change, and it can also distract them from it. [Heer and Robertson, *Animated Transitions in Statistical Data Graphics*](https://sites.stat.columbia.edu/gelman/communication/HeerRobertson2007.pdf) The practical unit is therefore an *event* that directs attention: the target you mean the viewer to see, the change that presents it, and enough time for the viewer to recognize it.

## Prominence is relative and temporary

Brightening the focal object may work in one frame and fail when a brighter particle burst enters nearby. An accent that stays on screen can fade into the background through repetition, while a rare change can become conspicuous. A scene written in code can name the intended order as roles (primary subject, supporting evidence, context, ornament) and change properties over time to keep that order. The order is a model to check against, and it does not predict exactly where attention goes.

**Attention** and **importance** are different things. A flash may catch the eye while a quiet choice tells the story, and the aim is to bring the two together at the right moment. For interfaces, Material Design describes focused motion as drawing attention to what matters without needless distraction, and the same question is useful to ask of video. [Material motion principles](https://m2.material.io/design/motion/understanding-motion/)

## What code makes inspectable

Scene objects can hold `role` and `focus` metadata next to position, scale, opacity, color, and motion. A render review can sample the start, the emphasis, and the hold of each event, then ask which element dominates at the size the video will be delivered. A grayscale view can show where tones compete; a muted view can show whether sound was covering for a weak visual signal. Neither view replaces watching the whole video.

For controls and rendered checks, see [Visual hierarchy and composition](../knowledge/Visual%20hierarchy%20and%20composition.md). For the time structure that gives the viewer time to register each change, see [Temporal visual rhythm](Temporal%20visual%20rhythm.md).

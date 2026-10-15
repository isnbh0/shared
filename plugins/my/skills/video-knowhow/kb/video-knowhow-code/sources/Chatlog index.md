# Chatlog source index

This index identifies the primary record behind the package. `C-<n>` means line `n` of the raw chatlog file, where each line holds one record; it is not a message number. The line and the UUID together identify a record even if the chatlog's database is rebuilt. Each citation's description helps you find the record; it does not independently verify claims made in the conversation.

Two chatlog files stay with John: the raw chatlog file (1,584 records; SHA-256 `fffbf828739fb17c651dde527cf268f25d2fdf7bada07f654102f86fded45a7e`) and a SQLite database built from it (`records.line_no`, `records.uuid`, `blocks`, and a `dialogue` view of human prompts and assistant messages). The source hash stored in the database matches the file's hash above. The C-anchor entries below are the package's finding aids, and the source hash and record UUIDs let anyone holding the raw file verify the records.

- The historical `ax-day/...` paths below are paths named *inside the chatlog*. Naming them does not mean those files are in this package.
- The chatlog is the earlier production's record; [content lineage](Content%20lineage.md) classifies the pages that cite it.

## Reading the evidence

A chatlog citation supports a [Reported](../Glossary.md#reported) claim, written `**Reported (chatlog):**`: the chatlog states that the thing was built, tested, or measured, and the package has not re-run it. That evidence is a tool call, its returned output, or code embedded in a tool call, and an outcome the assistant or John states, such as a finished render. A tool result can establish a command's exit status or media metadata; it does not establish how the finished image or music felt to a viewer. An assessment is not a Reported claim: pages quote the assistant's visual judgments and its web research summary as what the assistant said. A generalizable lesson drawn from this evidence is an [Interpretation](../Glossary.md#interpretation), and knowledge pages mark it separately.

This index does not independently verify third-party posts, 2026 model availability or pricing, media licensing, or the quality of the original videos. The assistant explicitly said it read the posts but did not watch the linked videos [C-231](#c-231), and that it could not listen to its own rendered audio [C-513](#c-513), [C-1146](#c-1146).

## Citation ledger

### C-10

- `uuid`: `7341407e-e04c-4729-a4d8-23877f692177`
- Evidence: John's request: investigate “opus5.5 video” on X and Threads and how it was made.

### C-231

- `uuid`: `ea841632-5726-449c-a456-c2a9293b8362`
- Evidence: Assistant's community research summary; explicitly says linked videos were not watched.

### C-245

- `uuid`: `d1bed600-4507-4595-a404-c2cf5a06de02`
- Evidence: John's request for a pre-stage intro video.

### C-313

- `uuid`: `13d1d8d2-426f-43be-bab4-da95b6300e06`
- Evidence: `intro/timeline.js` write call: beats, copy, event times, seeded typing jitter.

### C-329

- `uuid`: `9fbb61db-1c5c-461c-9247-59990ba76294`
- Evidence: `intro/index.html` write call: visual renderer source.

### C-346

- `uuid`: `b8724eca-4a80-4de8-9cd9-fa31481a2264`
- Evidence: `intro/render.js` write call: Chrome frame capture, still export, ffmpeg PNG pipe and audio mux.

### C-347

- `uuid`: `1cbf12a3-b5fc-4cc6-a651-40aeec9a0ee0`
- Evidence: First intro still-render command.

### C-398

- `uuid`: `4b1de912-c2ca-42da-94ee-c7eccbdd3b2b`
- Evidence: Contact-sheet image read during intro review.

### C-413

- `uuid`: `de6be241-5742-4c7f-83bb-9f212e01f7b0`
- Evidence: Intro visual correction after still review.

### C-424

- `uuid`: `8481adae-5c75-433b-8b33-62ff4a5adab7`
- Evidence: `intro/audio.js` write call: complete synthesized score and WAV export.

### C-444

- `uuid`: `6a45a7dc-2439-40d5-9b7a-0eeb0c2a5e07`
- Evidence: Tool result: 24-second WAV generation completed.

### C-459

- `uuid`: `4ca2691d-c2ee-450f-9e23-eeadffbf7b39`
- Evidence: Tool result: beat-window audio level measurements.

### C-493

- `uuid`: `63cf9993-88de-4904-bfe3-0e8d3f6cc831`
- Evidence: Tool result: intro render completed; ffmpeg reports 24-second MP4.

### C-499

- `uuid`: `01c80bd7-9716-468a-8dfb-c35c992733f2`
- Evidence: Read call for the intro contact sheet `final_sheet.png`.

### C-513

- `uuid`: `4f495b18-7588-4244-942c-9ff8fa18d42c`
- Evidence: Assistant's intro outcome, sequence, file map, unapproved event copy and unheard-audio caveat.

### C-522

- `uuid`: `d7505ad9-d50c-40f5-9323-1155ac420dd9`
- Evidence: John asks to test the method's limits against AI video generation.

### C-585

- `uuid`: `a5edfe00-38ee-4148-8e5c-9213b5431170`
- Evidence: Shared six-scene lab harness write call.

### C-586

- `uuid`: `7b51b331-332e-4e31-9c5d-b47c67a2b376`
- Evidence: Six-scene Chrome/ffmpeg renderer write call.

### C-621

- `uuid`: `d69f06e8-df8a-44f1-8ecd-ad023a5fcaca`
- Evidence: Human scene source: Canvas face, gradient shading, hair strands, blink, smile and simulated head turn.

### C-638

- `uuid`: `c3abf34f-8000-4550-8357-3baa846c21c4`
- Evidence: Cat scene source: four phased two-bone IK legs, walk-to-stop curve and head-view approximation.

### C-654

- `uuid`: `f19e35f2-125a-4a92-8b55-134064f22c73`
- Evidence: WebGL2 ocean fragment-shader source: procedural waves, ray march, normal, reflection, fog.

### C-702

- `uuid`: `32518e07-4312-431c-b090-5840af85951d`
- Evidence: Human-hair and ocean-shader revision, followed by still rerender.

### C-737

- `uuid`: `f754ba84-00b0-40bb-b156-5d9c9a00e4ec`
- Evidence: Photo scene source: image zoom, lake-row resampling, window glow, fireflies and newly drawn boat.

### C-738

- `uuid`: `4fd36478-ac34-453b-82b1-1f664dace363`
- Evidence: Fox scene source: triangular image mesh, localized deformation, overpainted blink and attempted head turn.

### C-739

- `uuid`: `d359404c-8cf9-4c76-a1ea-569bc5ef1044`
- Evidence: Data-chart scene source: five illustrative rows, bar interpolation, labels, values and percentages.

### C-767

- `uuid`: `3c80c81c-129b-4e94-b169-da1363e82c55`
- Evidence: Stills render command for photo, fox and chart scenes.

### C-794

- `uuid`: `7f23e119-baa5-4f31-95ef-19f347414a6b`
- Evidence: Code edit that resets leaked Canvas state.

### C-796

- `uuid`: `97c5bd6c-7f2b-4761-ae56-a47e3aa28b1a`
- Evidence: Tool output: all six five-second clips rendered after the chart-state fix; elapsed render times.

### C-805

- `uuid`: `e1c75c9c-cc78-42f7-b6d1-d344bc7fcd07`
- Evidence: Tool output: six rendered scenes each have 150 frames.

### C-812

- `uuid`: `cbf7c64b-b5a5-42e5-9338-5939fa83d08c`
- Evidence: Read call for a cat motion-frame sequence during review.

### C-818

- `uuid`: `94e63e94-7f0c-4ac7-870d-87bd350359fa`
- Evidence: Read call for a fox motion-frame sequence during review.

### C-837

- `uuid`: `b24ec418-c3dc-4566-b822-07f21325dcd5`
- Evidence: Tool call concatenating six clips into a test reel.

### C-846

- `uuid`: `f7a03b5b-5830-4883-98e7-6ce151f2b956`
- Evidence: Assistant's six-test assessment and researched comparison; model-market claims not independently checked here.

### C-854

- `uuid`: `76ceb70f-659b-42d1-8bcd-70b2d29c2e79`
- Evidence: John asks about other GPU shader tests and an Undertale-like pixel game.

### C-863

- `uuid`: `8e35876f-16de-4f23-bb28-2c40b41fb3f4`
- Evidence: Assistant's proposed shader tests and pixel-game components; these are proposals, not completed tests.

### C-869

- `uuid`: `80f3eb7c-47d1-47a8-9a79-590991a15daf`
- Evidence: John asks for an Undertale-style promotional trailer with appropriate technology chosen by the assistant.

### C-899

- `uuid`: `a205d37d-c0c4-43e3-aa13-83a3551bd146`
- Evidence: `foxtale/timeline.js` write call: dialogue timing, battle patterns, heart keyframes, music cues.

### C-926

- `uuid`: `e8b5387a-e699-4d95-8cbb-8983447c5d25`
- Evidence: `foxtale/sprites.js` write call: text-grid sprites and symmetry helper.

### C-942

- `uuid`: `c87ff8a6-d1b0-47a3-9ed8-1957745fd93f`
- Evidence: Sprite row-width validation and correction.

### C-953

- `uuid`: `cbb77a54-f38e-44c2-9145-47580c3a6c8b`
- Evidence: `foxtale/index.html` write call: Canvas scene implementation.

### C-969

- `uuid`: `2d853f71-f3bf-4c5e-acc1-d128efe1872b`
- Evidence: Pixel font copy and trailer renderer construction.

### C-1043

- `uuid`: `d57d8371-42cd-4d0a-b223-04b14755e3b8`
- Evidence: Trailer contact-sheet read after reviewing/correcting still selection.

### C-1070

- `uuid`: `90241f43-7988-44c7-92e7-31f1494eafb5`
- Evidence: Trailer visual corrections after still review.

### C-1081

- `uuid`: `7d03e88e-670e-4538-a6e1-a9578eb35cae`
- Evidence: `foxtale/audio.js` write call: note strings, original themes, chiptune voices, scene music and text blips.

### C-1112

- `uuid`: `aa5932dc-e917-4ed9-ac72-0c16ee945b72`
- Evidence: Tool output: 48-second WAV, 187 text blips, 1,440-frame render completed.

### C-1126

- `uuid`: `81ac8c22-0246-4b1b-a240-c602ad0bc25c`
- Evidence: ffmpeg probe output: 48-second H.264/AAC trailer at 1920×1080, 30 fps.

### C-1131

- `uuid`: `9519dca2-477f-431d-beeb-4480350d5001`
- Evidence: Read call for the trailer check image `final_check.png`.

### C-1146

- `uuid`: `d4e4a203-4300-4313-a125-c54bb3f919c1`
- Evidence: Assistant's trailer account, scene synopsis, technique choices, fixes, and unheard-audio caveat.

### C-1155

- `uuid`: `38801765-3240-4a17-9a02-124dafdfec7e`
- Evidence: John reports that the browser preview does not open.

### C-1234

- `uuid`: `a2c2dba5-5466-43fd-a36f-ba3d34fd1549`
- Evidence: `file://` probe output: black canvas and cross-origin `getImageData` SecurityError.

### C-1253

- `uuid`: `f65bff0a-09ff-499c-999e-aaa487b82b00`
- Evidence: Preview fix and `build_standalone.js`: audio-clock playback and inline scripts/fonts/image/audio.

### C-1264

- `uuid`: `424fedc8-3b08-43fa-acf6-07a2eb0e82fb`
- Evidence: Tool output: standalone preview has running audio at 3.94 seconds and no page errors.

### C-1286

- `uuid`: `609ceba0-03ca-4c76-ab0b-1d5a6916f271`
- Evidence: Browser-open command for standalone `foxtale.html`.

### C-1319

- `uuid`: `1327347b-408f-4295-a1ee-eddfa5eeb690`
- Evidence: Assistant's explanation of `file://` failure, standalone deliverable and click-to-play behavior.

### C-1328

- `uuid`: `a749ebb6-ac9a-4abc-b4c5-55658c471eb7`
- Evidence: John suggests pixel style may cover most work short of photorealism.

### C-1332

- `uuid`: `bfcba146-908f-4f43-99ae-57dc8c130636`
- Evidence: Assistant's refined boundary: rule-described detail versus hand-crafted visual/acting nuance.

### C-1452

- `uuid`: `d3336ebe-0bca-44ba-82f0-f5575ae44f41`
- Evidence: John asks for exploratory insight organization, not a prescriptive playbook or skill.

### C-1463

- `uuid`: `42a10fec-ffa1-49ca-be69-17d4356af816`
- Evidence: Write call for historical `notes/code-video-insights.md`.

### C-1520

- `uuid`: `2842d7e0-4a2c-4a0a-9aa8-383c00fe26c3`
- Evidence: Assistant's account of the revised insight document and its untested ideas; reported document contents, not independent test results.

### C-1532

- `uuid`: `7bc34c07-f1df-457b-a0f7-f24a143e17a0`
- Evidence: Assistant identifies missing detail in its earlier music documentation.

### C-1549

- `uuid`: `51e877af-4992-4059-8e9d-6c0de9a0dcd6`
- Evidence: Assistant distinguishes music-generation/sync outline from scene-level music direction.

The `blocks` table holds extracted text and tool arguments, and the `dialogue` view keeps only human prompts and assistant messages. In John's workspace, records are looked up by `line_no` or `uuid`.

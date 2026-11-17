# Team ownership development assets

`scene.py` creates an original room, three fictional adult characters, a physical board/marker, six cameras and baked poses. No external meshes, textures, likenesses or reference-media assets are included. Blender 4.3.2 was used.

Material revisions turn the torso/shoulders toward the board, move the leader aside, add gripping fingers/thumbs, place ink on the board surface and physically draw a connected idea. Actual stills and sampled motion positions were inspected. Read scene-preview-qa.json; full acting and overall editorial quality remain unverified.

One native 720×1280/24 fps frame render is active from an immutable source snapshot. Read ignored work/quality/active-handoff.json and its exact render status/session before starting anything. Do not duplicate it. The task-owned launcher holds a separate render lock and uses a source-hash-specific cache, partial PNG validation and a disk-space guard. A completed frame render still needs historical source-picture assembly, captions/context notices, final sound/picture review and finished source/QA records. Nothing here is ready to post.

Development stills are actually rendered at 432×768, 32 samples, without denoising or resizing. The motion test has 48 actually rendered 180×320 frames at 12 fps, sampling every second baked24fps pose; no optical interpolation is claimed. Full native frames remain in progress. This Blender build lacks bundled Open Image Denoise; the separately reviewed external tool has now processed three test frames and twelve more completed native frames. See `denoise-validation.json`; full temporal/editorial review remains pending.

The private .blend can be regenerated from source. In a future final edit, the historical interview occupies audio seconds7.36–14.16; these original scene frames do not replace it. The full-render flag skips that interval. Resume only the current frozen source and matching validated frame cache, not arbitrary files from an earlier revision.

`finishing-plan.json` records the actual prepared historical portrait input, its source upscale/frame selection, the complete frame mapping, preserved AAC-essence hash and outstanding caption/context checks. The historical picture remains private and silent; only the future assembled movie may become a candidate after real review. [Finishing workflow](../../../docs/production/2026-11-17-team-ownership-finishing.md).

`captions.ass` and `caption-validation.json` record the current speech-timed layout and actual sampled preflight inspection. The guarded assembler refuses missing, stale or unverified frame inputs; its caption-only and private historical-preflight modes do not create a finished Short. [Caption/assembly workflow](../../../docs/production/2026-11-17-team-ownership-caption-preflight.md).

`audio-preflight.json` records the existing male narration, continuous real interview excerpt, licensed music and original effects. Reuse the exact masters under ignored work/preproduction/jocko-give-the-team-the-plan/. No completed Short, ready candidate, service draft, schedule or published video exists for this concept.

The [four-second motion test](../../../examples/development/team-ownership/04-motion-test.mp4) contains the corresponding16.8–20.8second audio-plan window: generic male commentary, original marker effects and reviewed music. There are no authentic Jocko pictures or speech in that window. It has stereo48kHzAAC and a complete decode check. Sampled pictures and master ASR/measurements do not establish natural acting or subjective listening. `03-late-scene.png` is the current drawing still. `01-opening.png` and `02-marker-transfer.png` are earlier baselines, not final media.

Music credit: 'Ascension' by Scott Buckley - released under CC-BY 4.0. www.scottbuckley.com.au

Source: https://www.scottbuckley.com.au/library/ascension/ . License: https://creativecommons.org/licenses/by/4.0/ . Changes: excerpt trimmed, faded and ducked beneath original commentary and sound design. The full preflight music starts at track second122; the test uses its later16.8–20.8second window. No speaker, producer or composer endorsement is implied.

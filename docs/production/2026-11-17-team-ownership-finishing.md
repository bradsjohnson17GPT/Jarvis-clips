# Team ownership finishing preparation

The original native frame render is still running. No new finished Short, service draft, schedule or publication was created. The two existing revised male-voice drafts remain unchanged, and the rejected/failed Metricool copies remain held.

## Denoising

`scripts/denoise_original_frames.py` uses the reviewed Open Image Denoise 2.5.1 archive from config/denoiser.json. It verifies the pinned archive and installed runtime file bytes before execution, checks the frozen scene identity, processes only complete opaque native PNGs, preserves their dimensions and raw originals, and saves separate output hashes/receipts. Its CPU high-quality LDR/sRGB pass uses only the beauty image; it does not generate assets, resize pictures or replace the renderer.

Three native sample frames were processed and two actual outputs inspected for framing, faces and readable board lettering. Twelve more completed native frames were processed. A repeat on the original three samples returned zero new processing and three validated cache hits. [Validation](../../assets/stories/team-ownership/denoise-validation.json). This is a technical preflight; temporal consistency and full acting still need review after the complete movie exists.

Use the project's quality Python environment and existing reviewed release:

```sh
python scripts/denoise_original_frames.py \
  --render-root work/preproduction/jocko-give-the-team-the-plan/native-94b5afc8a78a \
  --oidn-archive /path/to/reviewed/oidn-2.5.1.tar.gz \
  --oidn-root /path/to/oidn-2.5.1.x86_64.linux --limit 24
```

Each invocation is a bounded batch over currently completed frames. Do not start a second renderer, re-filter cached outputs, denoise the historical source with this utility or infer editorial quality from completed checks.

## Historical picture and timing

The normal [official public embed](https://www.dvidshub.net/video/embed/718744) was checked again for advertised picture quality. It returned HTTP 200 and explicitly supplied only the previously reviewed 1024×576 playback file. No higher or gated media URL was guessed. The exact existing government source/rights scope remains unchanged.

A private working picture was prepared from source second 279.10. Its actual 324×576 crop at x=208/y=0 is scaled to 720×1280 with Lanczos. This is a documented 2.222… spatial upscale; encoding does not supply new source detail. Actual source timebase is 60000/1001 fps; output uses frame selection/drop to 24 fps, with no speed change or optical interpolation. The actual 163-frame working picture decoded completely and has no audio. Actual start/middle/end portrait samples were inspected: the face stays framed, division insignia is outside the crop, and shirt lettering remains incidental factual context. Do not claim all marks were removed or imply a speaker/company partnership.

The silent working picture is an input only. The already verified full soundtrack supplies the authentic statement, separate original generic male commentary, licensed music and original effects. It must not be replaced by unreviewed source audio or uploaded as a silent base.

[The finishing plan](../../assets/stories/team-ownership/finishing-plan.json) maps the expected 506-frame picture: original frames 1–177, 163 historical picture frames in positions 178–340, then original frames 341–506. At 24 fps this picture plan spans 21.0833 seconds; the existing audio master spans 21.0693 seconds. The quote's picture starts about 15 milliseconds after its audio-plan transition, within one delivery frame. Actual final synchronization and container duration must still be inspected.

The plan pins the existing AAC audio-essence hash for readback after stream-copying into the movie. Preserve exact narration/mix masters; regenerate nothing merely to assemble pictures. If a material audio change is needed, recheck the changed encoded soundtrack. Actual word timing is already available. Captions, illustration/source labels, exact nonendorsement notice, composer credit/source/license/changes, actual audience and the full final editorial/technical review remain before ready status. No paid research, purchases or outreach occurred.

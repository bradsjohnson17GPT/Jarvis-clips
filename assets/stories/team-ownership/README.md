# Team ownership development assets

`scene.py` creates the original room, three fictional adult character designs, physical board, marker, lights, six camera setups and baked pose curves. No external meshes, textures, likeness assets or reference-media files are included. Blender 4.3.2 was used.

This is an unfinished scene test. Six actual revised stills were inspected; three are preserved under examples/development/team-ownership/. Read `scene-preview-qa.json` before further work. Hand grips, torso orientation and visible drawing action need substantive improvement. The current actor motion and framing do not have a final editorial pass. Do not full-render repeatedly for cosmetic changes or treat passing renderer tests as permission to upload this scene.

```sh
blender -b -t 4 --python assets/stories/team-ownership/scene.py -- \
  --output /task-owned/work/team-ownership --preview
```

Previews are actually rendered at 432×768, 32 Cycles samples, without denoising or resizing. The planned delivery is 720×1280 at 24 fps; those full frame sequences have not been rendered. This Blender build lacks bundled Open Image Denoise. The separately reviewed external tool in config/denoiser.json is a possible later workflow, not something applied to these stills.

The private .blend can be regenerated from the source. The actual historical interview belongs at audio seconds 7.36–14.16 in a future final edit, not inside these original stills. The full-render flag skips that interval and resumes existing frame files; it is a development facility, not a ready-video or publishing workflow.

`audio-preflight.json` records the already generated male narration, continuous real interview excerpt, licensed music and original effects. Exact WAV/AAC masters and private receipts remain in ignored work/preproduction/jocko-give-the-team-the-plan/. Reuse them rather than synthesizing the same copy again. There is no completed movie, ready candidate, service draft, schedule or public video for this concept.

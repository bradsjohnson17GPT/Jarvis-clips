# Team ownership caption and assembly preflight

The native render remains active. No completed Short, ready-candidate entry, service draft, schedule or publication was created during this preparation. Existing Jocko/Goggins exact drafts and all held/published copies were preserved.

`scripts/assemble_team_story.py` prepares captions from the existing actual speech record. It preserves all 63 spoken words once in 24 cues, keeps narrator/real-speaker boundaries, adds illustration/source context and the exact required nonendorsement notice. Main caption placement changes with the shot to protect faces, the marker handoff and new idea. No narration, music or original effects were regenerated.

Actual captioned frames were inspected from native scene frame 84 and the historical preflight at local seconds 2.0/5.8. Main text, source identity and notice are readable in those samples. The source pictures and historical preflight remain private. The [original captioned native still](../../examples/development/team-ownership/05-captioned-native-frame84.png) is a development still, not upload media. Full acting, motion, final cuts and subjective soundtrack quality remain unverified; sampled frames and ASR are not continuous watching or listening.

The first private preflight exposed irregular timestamps. The corrected version uses frame-index timestamps and verified regular 24 fps: exactly 163 frames, 720×1280, 6.791667 seconds, stereo 48 kHz AAC and complete decode. The obsolete timing test must not be used. The full assembler avoids a video-frame cutoff that could truncate the audio path and checks actual encoded frame count/rate/duration.

The final assembly mode requires every matching native denoised frame, matching raw/output hashes, reviewed denoiser provenance, the inspected historical picture and exact audio input. An actual incomplete-input call was refused without creating a candidate file. It never substitutes a still, raw frame or placeholder for missing material.

A separate private test-pattern mux preserved the complete inspected AAC essence. That file is engineering evidence only, never content. Final real-video assembly must repeat the audio-essence readback and complete decode, then receive actual final editorial/audio/level/audience/source checks. Technical success alone leaves the output unpublishable.

```sh
python scripts/assemble_team_story.py \
  --render-root work/preproduction/jocko-give-the-team-the-plan/native-94b5afc8a78a \
  --picture-input work/preproduction/jocko-give-the-team-the-plan/jocko-portrait-picture-only.mp4 \
  --audio work/preproduction/jocko-give-the-team-the-plan/mixed-preflight.m4a \
  --work work/preproduction/jocko-give-the-team-the-plan/final-assembly
```

Without a video flag this prepares captions only. After all 343 original frames actually finish and have matching denoising receipts, add `--assemble --output` with a new task-owned candidate path. `--historical-preflight` is a mutually exclusive private layout test. No mode calls a publishing API or marks a candidate ready.

[Caption validation](../../assets/stories/team-ownership/caption-validation.json) and [finishing plan](../../assets/stories/team-ownership/finishing-plan.json) contain the exact hashes and outstanding requirements. Forty denoised original frames were available at this preparation checkpoint; remaining native rendering/processing continues. All 23 existing project checks passed. No paid research, purchases, outreach or repeated approval prompt occurred.

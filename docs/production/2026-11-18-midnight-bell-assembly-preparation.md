# Midnight Bell assembly preparation

The complete production animation is still rendering. The [finishing plan](../../assets/stories/midnight-bell/finishing-plan.json) and [assembler](../../scripts/assemble_midnight_story.py) now bind the eventual candidate to all 678 native frames, the unchanged scene/blend, receipt-verified same-size denoised images, the inspected V2 AAC and exact ASS captions. They create no queue entry or publishing draft.

The assembler checks every frame's raw and denoised hashes, scene identity and reviewed OIDN receipt. It has no raw-image or placeholder fallback. It copies AAC without re-encoding, burns the existing captions and verifies the encoded frame count, portrait dimensions, 24fps, separate video/audio/container durations, stereo 48kHz AAC, strict full decode and unchanged AAC essence. Outputs are new files inside ignored work/, with a separate assembly lock. A candidate remains subject to actual final review.

All **41 repository tests passed**, including an actual FFmpeg fixture mux that preserved the inspected AAC bytes and picture frame count. Failure tests cover missing denoised art, a substituted frozen blend, stale raw/denoise evidence, superseded audio and the earlier 72ms short-audio-tail failure even when overall video duration is correct. The fixture is synthetic test media, not a finished story or editorial-quality result. A check against the actual incomplete Midnight cache also refused assembly at a missing denoised frame, returned exit2 and created no movie.

Once the native and denoised sequences are complete, use the existing private V2 files:

```sh
python3 scripts/assemble_midnight_story.py \
  --render-root work/preproduction/midnight-bell/native-4dc6fe8ff851 \
  --audio work/preproduction/midnight-bell/audio-preflight-v2/mixed-preflight.m4a \
  --captions work/preproduction/midnight-bell/audio-preflight-v2/speech-and-context.ass \
  --assemble --output work/preproduction/midnight-bell/full-candidate-v1.mp4
```

The [new reveal review](../../assets/stories/midnight-bell/native-reveal-review.json) records 23 actual production-native captioned images, including every frame260–278 and later286/294/302/306;272 and306 were also viewed full-size. The wrench, bell and LED face are clear, and captions sit below the action. These are sampled images, not real-time playback or heard audio. A small caster/floor separation remains a final visual-review item; the active frozen scene was preserved. Low-battery acting, the charger connection, recovery, dawn callback and complete encoded pacing still need their finished production sequence.

Retain the inspected [V2 audio and caption preflight](2026-11-18-midnight-bell-audio-preflight.md). No narration, music, effects or captions were regenerated. Native rendering continues from the same pinned source without an overlapping render. Complete-film editorial release, sound/timing inspection and final levels remain separate from the assembler's technical checks. No new video is marked ready, scheduled or published.

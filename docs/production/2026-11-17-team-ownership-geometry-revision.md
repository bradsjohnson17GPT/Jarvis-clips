# Team ownership native geometry revision

The actual native return sample at 16.958 seconds largely hides the marker behind the near hand. The first native handoff close-up at 17.458 seconds makes the marker visible, but exposes hollow ends on the finger curves. The native return shot also partly crops the main colleague at the left edge. These findings came from actual 720×1280 frame samples, rather than continuous viewing or the earlier low-resolution motion test.

The revised original scene closes finger/thumb curves and adds matching rounded tips. Its return camera uses 49 mm instead of 53 mm to leave more room around the colleague. Character poses, story timing, authentic interview insert, recorded commentary, verified music mix and prepared captions are retained.

The revised scene is frozen at SHA-256 `974379894ff669312a943be008f47394b5ec91e41ecaf9a2c762b43754f40e42`. Its entire post-quote sequence, frames 341–506, must use the revised geometry. The reviewed opening, frames 1–177, retains original source `94b5afc8a78a063b857feaa4438a632dd370241c052c294878252e41db3f7791`, archived in [the original scene revision](../../assets/stories/team-ownership/revisions/scene-94b5afc8a78a.py). The same 163 reviewed historical picture frames fill positions 178–340.

The baseline renderer was deliberately stopped for this material fix. Its opening/cache is preserved; its old post-quote frames are superseded. One separate render cache holds the revised 166-frame section. Initial native review frames 408 and 420 are used by the eventual render and must be inspected before continuing. Frame files are never mixed under a false shared source hash.

The assembler now requires the revised cache through `--patch-render-root` and checks each native receipt against the source pinned for that shot. It rejects missing, wrongly versioned or truncated revision caches and cannot fall back to the old uncapped post-quote frames. All 27 tests passed, including four checks for source selection and rejection of stale/missing revision inputs.

After the revised native frames actually finish, denoise them with the reviewed utility and assemble using both approved caches:

```sh
python scripts/assemble_team_story.py \
  --render-root /path/to/original-opening-cache \
  --patch-render-root /path/to/revised-postquote-cache \
  --picture-input /path/to/reviewed-historical-picture.mp4 \
  --audio /path/to/existing-verified-mix.m4a \
  --work /path/to/new-private-assembly \
  --assemble --output /path/to/new-private-candidate.mp4
```

Actual grip/contact, marker ownership change, writing, cuts, full temporal consistency, captions, source transition, final encoded audio and audience still need review. Technical checks and a corrected still do not establish a final quality pass. This is the same existing teamwork concept; it remains outside the ready/posting queue. No new service draft, schedule or publication has been created.

The two actual revised native samples have now been denoised with matching source/output receipts and inspected with the existing captions. Frame 408 fully frames both main faces, although the pre-transfer pose still largely hides the marker. Frame 420 clearly shows the marker and closed rounded tips. These samples support rendering the revised shot sequence; the later contact/ownership change, drawing and continuous motion remain unreviewed. [Actual sample evidence](../../assets/stories/team-ownership/return-shot-preflight.json).

Six additional actual native poses were rendered and denoised in the same frozen cache: 426, 429, 432, 453, 478 and 498. The marker is visible between the hands in the contact samples. The teal-sleeved colleague later holds it at the board; a branch extends from the original blue idea and the closed new node is visible at the end. Captions remain readable. The drawing shot partly crops the board heading, while its new branch/node remains clear. These are sampled poses, not continuous viewing: the full release/withdrawal motion, acting, cuts and assembled sequence remain for final review. The remaining render reuses these valid frames.

The subsequent [frame-by-frame handoff review](../../assets/stories/team-ownership/handoff-frame-review.json) covers every native frame419–441, including the complete close-up 420–439 and both adjacent cuts. The marker stays visible through shared contact; the leader's hand withdraws across 434–439 while the teal-sleeved teammate retains it. The cut at 440 preserves that ownership. Closed rounded fingertips and readable captions remain consistent across these 23 actual frames. This resolves the earlier unreviewed withdrawal finding within this shot. It is not real-time playback, subjective audio listening or a full-story quality pass: the complete drawing motion, pacing, source transition and encoded final movie remain to inspect.

The existing source-frozen render continues in its same cache. A separate private local finishing process waits for that render's successful 166-frame completion, validates/denoises its outputs, and uses the existing guarded assembler to create a private 506-frame candidate with the unchanged verified AAC soundtrack. It never starts another render, changes a posting queue, creates a service draft or publishes. Its output remains explicitly pending actual editorial review; inspect its private status before starting overlapping finishing work.

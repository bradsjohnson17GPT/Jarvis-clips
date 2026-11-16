# Jarvis Clips

Creates portrait comedy videos from footage with reviewed reuse rights. This first version renders silent videos with original captions, keeps license records, and saves downloadable files through GitHub Actions.

## Watch the first draft

[Watch the small preview](examples/first-short-preview.mp4) · [Download the full-resolution draft](examples/first-short.mp4).

The example is a 7.5-second dog-and-cat clip with an original office joke. It is a draft with no audio, not a promise of monetization. The footage is from [Pexels](https://www.pexels.com/video/a-dog-and-a-cat-playing-9400102/) under the [Pexels License](https://www.pexels.com/license/).

## Get a finished video without installing software

1. Open the **Actions** tab in this repository.
2. Select **Render Shorts**, then **Run workflow**.
3. Open the finished run and download its **jarvis-clips** artifact.
4. Each clip folder contains `video.mp4`, its captions, and `metadata.json` with source and license records.

The workflow also runs when the renderer, clip manifests, or batch selection changes. `batches/current.json` selects up to ten distinct manifests per run; older manifests remain available without being reposted. It does not invent ten variations of one video to fill a quota.

## Run locally

Requires Python 3.10+, FFmpeg with libass/libx264, and DejaVu Sans. No Python packages or paid API are required.

```sh
python3 -m unittest discover -s tests
python3 scripts/render.py clips/spreadsheet.json
```

To use a source already downloaded:

```sh
python3 scripts/render.py clips/spreadsheet.json --source-file /path/to/source.mp4
```

## Add another video

Add a JSON manifest under `clips/`, using `spreadsheet.json` as the template. Set the source page, download URL, license URL, review date, reviewer, explicit audience, original script, and accurate timing. A rights flag is a recorded human/assistant review, not an automatic legal check. The renderer refuses missing rights declarations, missing audience classifications, invalid timing, overlapping captions, and unsafe clip identifiers.

## Test content and adapt

The initial plan tests five content types with two posts each: animal POV, workplace comedy, everyday humor, visual surprises, and fictional micro-stories. After at least three comparable mature clips per type, `scripts/experiments.py` proposes five slots for the strongest type, two for the next, and three exploration slots. It uses median views and secondary retention/sharing evidence, rather than one viral outlier. Until enough data exists, it stays balanced.

See [the experiment and reporting policy](docs/strategy.md) and [the configuration](config/strategy.json). A separate chat task reports platform-reported estimated revenue at **9 a.m. Pacific**; financial records stay private. This is a scheduled task, not a guarantee of earnings or paid-out profit.

Every output is 720 × 1280, H.264, 30 fps, with audio removed. Landscape sources retain the whole frame over a blurred background. Sources already at 9:16 can use `layout: portrait` to fill the video without artificial side panels. Captions are burned into the video.

## Publishing status

- Daily target requested: **10 distinct original Shorts**.
- November 16 batch: **10 confirmed pending Shorts**, two per content type, scheduled from 9 a.m. through 9 p.m. Pacific. [Batch verification and schedule](docs/production/2026-11-16.md).
- First Short: **scheduled through Metricool for November 16, 2026, at 4 p.m. Pacific**. Metricool imported the MP4 and confirmed a pending YouTube post; it has not yet published. See `state/queue.json` to avoid rescheduling it.
- Editing: implemented and tested on the example clip.
- Source record: included in each manifest and rendered output.
- Downloadable preview: included in `examples/`.
- Publishing is handled through the connected Metricool chat tools. The first transfer and scheduling request succeeded using the public example MP4 URL; Metricool copied the video into its own storage. The Python renderer itself does not publish. GitHub Actions artifacts require authentication, so future clips still need a reachable media URL for import. Changing repository visibility would remove unauthenticated GitHub raw access.
- No video is marked as published by this renderer. An output file is not a confirmed YouTube post.

GitHub workflows run as jobs and do not guarantee six continuous hours of daily work. The existing chat task is separate from this on-demand rendering workflow.

## Credentials and costs

Do not commit passwords, OAuth tokens, `.env` files, or personal account identifiers. If publishing credentials are added later, use GitHub Actions secrets or an approved account connection. Private repositories may have limited included Actions minutes; this project does not purchase capacity or services.

# Jarvis Clips

Creates portrait comedy videos from footage with reviewed reuse rights. This first version renders silent videos with original captions, keeps license records, and saves downloadable files through GitHub Actions.

## Watch the first draft

[Download or watch the first draft](examples/first-short-preview.mp4).

The example is a 7.5-second dog-and-cat clip with an original office joke. It is a draft with no audio, not a promise of monetization. The footage is from [Pexels](https://www.pexels.com/video/a-dog-and-a-cat-playing-9400102/) under the [Pexels License](https://www.pexels.com/license/).

## Get a finished video without installing software

1. Open the **Actions** tab in this repository.
2. Select **Render Shorts**, then **Run workflow**.
3. Open the finished run and download its **jarvis-clips** artifact.
4. Each clip folder contains `video.mp4`, its captions, and `metadata.json` with source and license records.

The workflow also runs when the renderer or clip manifests change. It processes up to ten distinct manifests per run. It does not invent ten variations of one video to fill a quota.

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

Every output is 720 × 1280, H.264, 30 fps, with audio removed. The foreground retains the whole source frame over a blurred background. Captions are burned into the video.

## Publishing status

- Daily target requested: **10 distinct original Shorts**.
- Editing: implemented and tested on the example clip.
- Source record: included in each manifest and rendered output.
- Downloadable preview: included in `examples/`.
- YouTube/Metricool publishing: **not implemented in this code**. A connected chat tool can schedule inspected videos only after it has a reachable media URL and a valid scheduling response. GitHub Actions artifacts require authentication and are not direct public media URLs.
- No video is marked as published by this renderer. An output file is not a confirmed YouTube post.

GitHub workflows run as jobs and do not guarantee six continuous hours of daily work. The existing chat task is separate from this on-demand rendering workflow.

## Credentials and costs

Do not commit passwords, OAuth tokens, `.env` files, or personal account identifiers. If publishing credentials are added later, use GitHub Actions secrets or an approved account connection. Private repositories may have limited included Actions minutes; this project does not purchase capacity or services.

Current revised pilot: [The Downward Beacon — finished video with sound](media/quality/downward-beacon.mp4). Its original scene sources, score credit and measured QA are recorded in [media/quality](media/quality/README.md). The rejected bulk batch stays held; this link is a finished preview, not publication evidence.

> Quality reset, November 16: the owner rejected the previous format. The 30 unpublished posts are now held as drafts with automatic publication disabled. Ten earlier posts were confirmed published. No old draft should be re-enabled to fill a quota. See [quality direction](docs/quality.md).

# Jarvis Clips

Creates original portrait comedy and motivational videos from footage with reviewed reuse rights. New videos include timed narration, reviewed music and light effects, original captions, source records, and downloadable files through GitHub Actions.

## Watch the first draft

[Watch the small preview](examples/first-short-preview.mp4) · [Download the full-resolution draft](examples/first-short.mp4).

The example is a 7.5-second dog-and-cat clip with an original office joke. Its latest version includes narration and original background audio. The footage is from [Pexels](https://www.pexels.com/video/a-dog-and-a-cat-playing-9400102/) under the [Pexels License](https://www.pexels.com/license/).

## Get a finished video without installing software

1. Open the **Actions** tab in this repository.
2. Select **Render Shorts**, then **Run workflow**.
3. Open the finished run and download its **jarvis-clips** artifact.
4. Each clip folder contains `video.mp4`, its captions, and `metadata.json` with source and license records.

The workflow also runs when the renderer, clip manifests, or batch selection changes. `batches/current.json` selects up to twenty distinct manifests per run; older manifests remain available without being reposted. It does not fill the target with variations of one video.

## Run locally

Requires Python 3.10+, FFmpeg with libass/libx264, DejaVu Sans, and locally installed narration dependencies. No paid API is required. See [audio setup and rights](docs/audio.md).

```sh
python3 -m venv work/audio-venv
work/audio-venv/bin/python -m pip install -r requirements-audio.txt
work/audio-venv/bin/python scripts/download_voice.py
work/audio-venv/bin/python -m unittest discover -s tests
work/audio-venv/bin/python scripts/render.py clips/spreadsheet.json
```

To use a source already downloaded:

```sh
work/audio-venv/bin/python scripts/render.py clips/spreadsheet.json --source-file /path/to/source.mp4
```

## Add another video

Add a JSON manifest under `clips/`, using `spreadsheet.json` as the template. Set the source page, download URL, license URL, review date, reviewer, explicit audience, original script, and accurate timing. A rights flag is a recorded human/assistant review, not an automatic legal check. The renderer refuses missing rights declarations, missing audience classifications, invalid timing, overlapping captions, and unsafe clip identifiers.

## Test content and adapt

The initial plan tests five content types with four posts each: animal POV, workplace comedy, everyday humor, visual surprises, and fictional micro-stories. After at least three comparable mature clips per type, `scripts/experiments.py` proposes eight slots for the strongest type, four for the next, and eight exploration slots. It uses median views and secondary retention/sharing evidence, rather than one viral outlier. Until enough data exists, it stays balanced.

See [the experiment and reporting policy](docs/strategy.md) and [the configuration](config/strategy.json). A separate chat task reports platform-reported estimated revenue at **9 a.m. Pacific**; financial records stay private. This is a scheduled task, not a guarantee of earnings or paid-out profit.

Every output is 720 × 1280, H.264, 30 fps. Source audio is removed and replaced with reviewed narration and original music/effects. Landscape sources retain the whole frame over a blurred background. Sources already at 9:16 can use `layout: portrait` to fill the video without artificial side panels. Captions are burned into the video.

## Publishing status

- Daily posting target: **20 distinct original Shorts**, raised after the owner requested more frequent posts.
- Audio update: all nine pending November 16 posts now use narration, original music, and effects. The already-live cat Short is retained as published. [Audio verification](docs/production/2026-11-16-audio.md).
- Latest noon verification: **November 16: 5 published and 15 pending; November 17: 20 pending**. Two motivational pilots are in today's existing slots; tomorrow has twenty new distinct Shorts. [Latest verification](docs/production/2026-11-17.md).
- First Short: **scheduled through Metricool for November 16, 2026, at 4 p.m. Pacific**. Metricool imported the MP4 and confirmed a pending YouTube post; it has not yet published. See `state/queue.json` to avoid rescheduling it.
- Editing: implemented and tested on the example clip.
- Source record: included in each manifest and rendered output.
- Downloadable preview: included in `examples/`.
- Publishing is handled through the connected Metricool chat tools. The first transfer and scheduling request succeeded using the public example MP4 URL; Metricool copied the video into its own storage. The Python renderer itself does not publish. GitHub Actions artifacts require authentication, so future clips still need a reachable media URL for import. Changing repository visibility would remove unauthenticated GitHub raw access.
- No video is marked as published by this renderer. An output file is not a confirmed YouTube post.

GitHub workflows run as jobs and do not guarantee six continuous hours of daily work. The existing chat task is separate from this on-demand rendering workflow.

## Credentials and costs

Do not commit passwords, OAuth tokens, `.env` files, or personal account identifiers. If publishing credentials are added later, use GitHub Actions secrets or an approved account connection. Private repositories may have limited included Actions minutes; this project does not purchase capacity or services.

## Trend-watching agent

[The trend scout](agents/trend-scout.md) researches current comedy three times daily and passes dated video analyses and original adaptation ideas to production. vidIQ is connected for public video analysis; publishing continues through Metricool. The normal target cadence is every 40 minutes from 8 a.m. to 8:40 p.m. Pacific, with existing daily slots retained as needed. Production checks run approximately every four hours, including midnight and 4 a.m.; concise progress updates follow morning and afternoon runs. The 9 a.m. earnings report remains unchanged. Scheduled checks do not guarantee uninterrupted runtime.

## Streamer and gaming highlights

The owner's latest direction adds real streamer highlights and GTA VI launch coverage. The supplied Minecraft rescue example was analyzed for actual scenes and audio: immediate danger, short context, then a genuine rescue. [Reference analysis](docs/trends/2026-11-16-streamer-reference.md) · [workflow](agents/streamer-scout.md) · [source review status](state/streamer-queue.json). The recurring scout and production tasks now prioritize this lane. No current/live streamer source has been commercially cleared, no streamer clip has been posted, and Twitch login or continuous live viewing is not established. Existing original Shorts remain queued; the separately reviewed historical motivational pilot is not streamer footage.

## Motivational Shorts

The owner's three motivational examples were analyzed for real video/audio pacing. The new experiment uses original messages, energetic reviewed music, and independently licensed footage or documented factual editorial archival use. See config/motivation.json and docs/audio.md. Famous people's social uploads, films and speeches are not automatically cleared merely because they are public.

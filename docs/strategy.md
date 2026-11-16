# Content experiments and reporting

The owner authorizes routine research, editing, posting, scheduling, code changes, and adjustment without repeated confirmation. Work through actual connected tools and permissions. Record a blocked operation accurately; permission does not grant missing account access or continuous runtime. Keep routine user-facing updates to the daily money report.

## Initial test

Aim for twenty distinct, inspected Shorts per day across five types, initially four each:

| Type | Format |
| --- | --- |
| animal_pov | Original animal point-of-view comedy |
| workplace_comedy | Office and work jokes, including the first spreadsheet Short |
| everyday_humor | Relatable everyday-life situations and original observations |
| visual_surprises | Satisfying or surprising visuals with an original hook and payoff |
| fictional_micro_stories | Short original fictional stories, clearly presented as fiction |

Use independently reviewed source footage and original scripts. Do not fill the posting target with nearly identical versions of one clip. Expand formats as well as topics. Rotate posting times so one type is not always assigned the strongest time. Keep the channel aimed at teens and adults; classify every actual video appropriately.

Tag each manifest and queue entry with `content_type`, `hook_type`, `duration`, source identity, and actual publication time when known. Scheduled time is not proof of publication. Count previously scheduled/published videos toward the daily target. Never publish the sample again simply because the renderer produced a new artifact.

## Measure before adjusting

Capture timestamped per-video analytics with actual publication time, collection time, views, duration, average view duration, shares, and the available collection window. Keep snapshots in ignored `work/analytics/`, not the public repository. A daily analytics range is not necessarily a video's lifetime total: label the exact window and never mix measurement scopes.

Compare videos at 48-54 hours old using the same measurement scope. Do not describe a lifetime counter as first-day views. The analysis script accepts observations already normalized to comparable cumulative-to-snapshot views. If the API only returns a selected date-range count, normalize it with correctly dated snapshots first or wait for comparable data. Do not fabricate a missing metric.

Use `scripts/experiments.py` to propose an allocation. It ignores incomplete/invalid observations, keeps one qualifying observation per distinct clip, and requires at least three distinct qualifying clips for every type. Start balanced while data is insufficient. Compare median views; use average view duration divided by clip length and shares per thousand views as secondary evidence when available. Loops may produce a duration fraction above one.

Once enough comparable evidence exists, allocate ten slots to the leading type, four to the next, and two to each other type. This preserves six exploration slots. Rankings are provisional observations, not causal proof or a guarantee of more views. Reevaluate as new data arrives; keep historical snapshots so late API corrections and changes in audience can be detected. If measurements are stale or evidence is no longer comparable, return to balanced testing rather than claiming a current winner.

```sh
python3 scripts/experiments.py
python3 scripts/experiments.py --observations work/analytics/comparable-observations.json
```

Normalized observations are a JSON array. Each object uses `clip_id`, `content_type`, `age_hours`, and `views`; optional fields are `duration_seconds`, `average_view_duration_seconds`, and `shares`. Include actual source windows and timestamps in the private raw snapshot records used to create that array. Never count the same clip multiple times because multiple snapshots exist.

## Daily money report

A separate chat task runs at **9 a.m. America/Los_Angeles**, using `exact_schedule`. Production checks run around 6 a.m., noon, and 6 p.m.; task runs do not guarantee six continuous hours of work. The 9 a.m. report should contain only the previous complete day's reported estimated revenue and a brief source delay/access note when necessary.

Use the connected YouTube channel's nondeprecated channel-level revenue metric (currently `YTEV03`) from Metricool. Request revenue by itself and inspect the returned dates. Do not sum a channel total with per-video amounts or infer money from views. If yesterday is missing, check up to seven earlier days and label the latest available period. Missing data is **unavailable**, not zero. A numeric zero is valid only when the source returns it explicitly for that day. Verify currency; do not invent a dollar denomination when the source provides none.

YouTube analytics revenue is a platform estimate, not a bank payout or net profit. Report actual payments only with payment evidence. Deduct costs only if verified cost records exist; do not claim unverified profit. Do not publish financial data or personal account identifiers to this public repository. Store snapshots in ignored `work/reports/` or `work/analytics/` and deliver the report in the private chat.


## Audio standard

The user requested audio on November 16. New posts require timed narration, original or independently licensed quiet music, and appropriate original effects; see `docs/audio.md`. Record the audio version with each queue entry and performance snapshot so a silent legacy post is not treated as a fully comparable audio-format sample. Never republish an already-live clip solely to add sound.

## Trend scout and faster posting

The user requested funnier, timely content and more frequent posts. The daily target is now 20. A normal full-day schedule starts at 8 a.m. Pacific with 40-minute intervals, finishing at 8:40 p.m. Existing scheduled times may be retained while open gaps are filled, maintaining at least 25 minutes between posts and at most 20 total per Pacific date. Today's original ten keep their existing times.

The recurring trend scout checks around 5 a.m., 11 a.m., and 5 p.m., using `agents/trend-scout.md` and `config/trends.json`. Production consumes `state/trend-brief.json`, uses independently licensed footage and original scripts/audio, and prioritizes a visible setup, complication, and payoff. Midday/evening production can fill unused daily slots or replace up to four pending trend-test slots per day, at least 30 minutes before their posting time, without increasing the daily total. Only production publishes. Record trend references and audio versions alongside the content type, while keeping financial and account analytics private. Never call a video watched from title metadata alone.

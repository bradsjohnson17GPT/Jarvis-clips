#!/usr/bin/env python3
"""Suggest content slots from comparable, privately collected video snapshots."""
import argparse
import json
import math
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]


def nonnegative(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


def plan(config, observations):
    types = config["content_types"]
    minimum = config["minimum_distinct_clips_per_type"]
    start = config["comparison_age_hours"]
    end = start + config["comparison_age_tolerance_hours"]
    chosen = {}
    for row in observations:
        if not isinstance(row, dict):
            continue
        identity, kind = row.get("clip_id"), row.get("content_type")
        age, views = row.get("age_hours"), row.get("views")
        if not isinstance(identity, str) or not identity or kind not in types:
            continue
        if not nonnegative(age) or not nonnegative(views) or not start <= age <= end:
            continue
        if identity in chosen and chosen[identity]["content_type"] != kind:
            raise ValueError(f"Conflicting content types for clip {identity}")
        # One snapshot per clip, taken as close to the common comparison age as possible.
        if identity not in chosen or age < chosen[identity]["age_hours"]:
            chosen[identity] = row
    groups = {kind: [r for r in chosen.values() if r["content_type"] == kind] for kind in types}
    ranking = []
    for kind, rows in groups.items():
        fractions, rates = [], []
        for row in rows:
            duration, watched = row.get("duration_seconds"), row.get("average_view_duration_seconds")
            if nonnegative(duration) and duration > 0 and nonnegative(watched):
                fractions.append(watched / duration)
            shares = row.get("shares")
            if row["views"] > 0 and nonnegative(shares):
                rates.append(shares * 1000 / row["views"])
        ranking.append({
            "content_type": kind,
            "distinct_clips": len(rows),
            "median_views": median([r["views"] for r in rows]) if rows else None,
            "median_average_view_duration_fraction": median(fractions) if fractions else None,
            "median_shares_per_1000_views": median(rates) if rates else None,
        })
    ranking.sort(key=lambda r: tuple(r[k] if r[k] is not None else -1 for k in config["ranking"]), reverse=True)
    qualified = all(len(rows) >= minimum for rows in groups.values())
    enough_signal = qualified and ranking[0]["median_views"] > 0
    if enough_signal:
        winner_slots = config["adaptive_winner_slots"]
        slots = {r["content_type"]: (winner_slots[i] if i < len(winner_slots) else config["adaptive_exploration_slots_per_other_type"]) for i, r in enumerate(ranking)}
    else:
        slots = dict(config["initial_slot_allocation"]) if "initial_slot_allocation" in config else {kind: config["initial_slots_per_type"] for kind in types}
        if set(slots) != set(types):
            raise ValueError("Initial slot allocation must cover each active content type")
    if sum(slots.values()) != config["daily_post_target"]:
        raise ValueError("Configured slots do not match the daily post target")
    return {
        "mode": "adaptive" if enough_signal else "balanced",
        "reason": "Provisional ranking from comparable observations" if enough_signal else "Insufficient comparable clips or no positive view signal",
        "daily_slots": slots,
        "ranking": ranking,
        "note": "Count existing scheduled clips toward these totals; this script does not schedule or publish."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/strategy.json")
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    observations = json.loads(args.observations.read_text()) if args.observations else []
    print(json.dumps(plan(config, observations), indent=2))


if __name__ == "__main__":
    main()


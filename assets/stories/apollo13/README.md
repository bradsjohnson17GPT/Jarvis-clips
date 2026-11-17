# Apollo 13 explanatory development

Original procedural animation with one individually reviewed NASA photograph. It is a simplified factual explanation, not an engineering reconstruction, physical simulation or emergency-device guide. No mixed-source documentary, private creator footage, third-party character/model or source soundtrack is used.

The v2 preview in examples/development/ replaces the original opaque fitting with flexible plastic, a visible card insert and tape seals. A ground-team design/test to crew-assembly relay follows the spoken sequence. Exact native cut frames and material/relay samples were inspected. Its encoded soundtrack is byte-identical to the ASR-verified v1 mix; no new narration or music encode was needed.

It remains a development alternate, outside the ready/posting queues. Its largely technical presentation has less human action and emotional progression than the owner's references. Prioritize stronger cleared people/action footage rather than repeatedly polishing this alternate without a material reason. This is an editorial selection decision, not a measured performance failure or a request for owner permission.

Use the quality virtual environment. render_explainer.py takes --photo, --timing and --output; inspect --stills-only first. finish_explainer.py takes --story, --picture, --narration, --music and --output. It verifies the source-photo/music hashes and uses the pinned male narrator. Reuse the actual private narration master and timing if present. A clean checkout must retrieve the exact reviewed NASA photo and score, and regenerate the pinned narration only if the private master is unavailable.

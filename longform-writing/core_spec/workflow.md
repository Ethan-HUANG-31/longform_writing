# Workflow V0

1. `parse_request`
   - Save the raw user request to `00_request.md`.
   - Parse minimum fields: language, genre, scale, premise, constraints, mode.

2. `build_project_brief`
   - Generate `01_project_brief.md`.
   - Confirm premise, protagonist, tone, POV, constraints, forbidden content, default assumptions.

3. `build_codex`
   - Generate `02_codex.json`.
   - Include global/always-include entries and relevant character/location/object/rule entries.

4. `generate_outline`
   - Generate `03_outline.json`.
   - Use 3 chapters by default. Each chapter should include `required_codex` when useful.

5. For each chapter:
   - `generate_chapter_summary` -> `chapters/chapter_XX/00_summary.md`
   - `generate_scene_beats` -> `chapters/chapter_XX/01_beats.json`
   - `validate_scene_beats` -> manifest/log validation result
   - `write_beat_prose` -> `chapters/chapter_XX/02_draft.md`
   - `summarize_chapter` -> `chapters/chapter_XX/03_summary_after.md`

6. `merge_manuscript`
   - Concatenate chapter drafts into `manuscript/draft_full.md`.
   - Copy to `manuscript/final.md` for V0.

## Milestone Review Mode

Pause at:

1. after project brief
2. after Codex and outline
3. after chapter 1 draft and summary_after

Apply feedback upstream, invalidate downstream outputs, and resume.

## Workflow V1: Chapter Revision Loop

V1 starts from the V0 full-skill manuscript and revises chapter by chapter before final assembly.

For each chapter:

1. `review_chapter_quality`
   - Review the current chapter draft against the fixed quality rubric and continuity context.
   - Output `chapters/chapter_XX/04_chapter_review.json` and `chapters/chapter_XX/04_chapter_review.md`.

2. `plan_chapter_revision`
   - Produce a focused revision plan for real prose improvement while preserving story facts.
   - Output `chapters/chapter_XX/05_revision_plan.json` and `chapters/chapter_XX/05_revision_plan.md`.

3. `rewrite_chapter`
   - Rewrite the chapter from the plan, using Codex, outline, chapter context, and prior summaries.
   - Output `chapters/chapter_XX/02_revised_draft.md`.

4. `summarize_revised_chapter`
   - Summarize the revised chapter for downstream continuity.
   - Output `chapters/chapter_XX/03_summary_after_revised.md`.

After all chapters:

1. `merge_revised_manuscript`
   - Assemble the revised chapter drafts into the revised full manuscript.
   - Preserve `manuscript/final_unrevised.md` and output `manuscript/final_revised.md`.

2. Build the four-way blind package:
   - `direct_write`
   - simple engineered
   - full skill unrevised
   - full skill revised (`full_revised`)

3. Evaluate the blind package with:
   - Rubric Judge
   - Reader/Editor Judge

4. Iterate the chapter revision loop up to 3 times.

Success requires `full_revised` to beat `direct_write` in blind real-text quality while preserving longform continuity.

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


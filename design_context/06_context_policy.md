# Context Policy V0

The workflow should control context explicitly. Do not pass the full project state to every step.

Every generation or validation step should also write trace records:

- append one entry to `run_records/step_manifest.jsonl`
- save the rendered prompt to `run_records/rendered_prompts/{step_id}.md`
- record input files, output files, prompt template, and context sections

## Global Context

Usually available:

- `01_project_brief.md`
- global/always-include entries from `02_codex.json`

Codex context is split into:

- `Global Codex`: entries with `always_include: true`, such as style, premise, central rules, and hard constraints.
- `Relevant Codex`: entries selected by `required_codex`, exact name/alias match in the current chapter summary or beat, or manual additional context.

Do not implement complex semantic retrieval in V0.

## Build Project Brief

Read:

- user request

Write:

- `01_project_brief.md`

## Build Codex

Read:

- `00_request.md`
- `01_project_brief.md`

Write:

- `02_codex.json`

Context should focus on stable facts, not chapter prose.

V0 should infer obvious stable entries from the request and project brief, then mark them as either `global` or `relevant`. It should not attempt ongoing automatic Codex extraction after every chapter.

## Generate Outline

Read:

- `01_project_brief.md`
- `02_codex.json`, prioritizing global entries and core protagonist/setting entries

Write:

- `03_outline.json`

The outline should be concrete enough to generate chapter summaries and beats.

## Generate Chapter Summary

Read:

- `01_project_brief.md`
- global Codex entries
- Codex entries named in the outline chapter, if any
- one chapter entry from `03_outline.json`
- previous chapter `03_summary_after.md` files if available

Write:

- `chapters/chapter_XX/00_summary.md`

## Generate Scene Beats

Read:

- `01_project_brief.md`
- global Codex entries
- relevant entries from `02_codex.json`
- `chapters/chapter_XX/00_summary.md`
- previous chapter summaries if available

Write:

- `chapters/chapter_XX/01_beats.json`

Beats should contain enough named references to support later Codex retrieval. When possible, each beat should include `required_codex`.

## Validate Scene Beats

Read:

- `chapters/chapter_XX/00_summary.md`
- `chapters/chapter_XX/01_beats.json`
- previous chapter summaries
- global Codex
- relevant Codex

Write:

- validation result, either inline in log or a future `01_beats.validation.json`
- rendered validation prompt under `run_records/rendered_prompts/`
- manifest entry in `run_records/step_manifest.jsonl`

V0 can keep validation lightweight.

## Write Beat Prose

Read:

- `01_project_brief.md`
- global Codex entries
- relevant `02_codex.json` entries selected by `required_codex` and name/alias matches
- previous chapter summaries as story so far
- `chapters/chapter_XX/00_summary.md`
- current chapter text before the current beat
- current beat from `01_beats.json`

Write:

- append to `chapters/chapter_XX/02_draft.md`
- rendered prose prompt under `run_records/rendered_prompts/`
- manifest entry in `run_records/step_manifest.jsonl`

Do not include future chapter summaries or final twist notes unless the current chapter requires them.

## Summarize Chapter

Read:

- `chapters/chapter_XX/02_draft.md`

Write:

- `chapters/chapter_XX/03_summary_after.md`

The summary should be factual, compact, and useful as future memory.

## Merge Manuscript

Read:

- all `chapters/chapter_XX/02_draft.md`

Write:

- `manuscript/draft_full.md`
- `manuscript/final.md`

In V0, `final.md` may equal `draft_full.md`.

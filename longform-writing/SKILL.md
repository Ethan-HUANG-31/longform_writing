---
name: longform-writing
description: Create and run a structured longform fiction writing workflow. Use when the user wants to draft a novel/short story through project brief, Codex/story bible, outline, chapter summaries, scene beats, beat-level prose, summary-after memory, manuscript assembly, milestone review, or acceptance testing with traceable prompts and run records.
---

# Longform Writing

Use this skill to draft longform fiction through structured intermediate files. Do not generate the whole story directly from the original request.

## Core Workflow

Follow this sequence:

```text
User Request -> Project Brief -> Codex -> Outline -> Chapter Summary -> Scene Beats -> Beat Validation -> Beat Prose -> Summary After -> Manuscript
```

Each run creates a writing project directory:

```text
runs/{project_slug}/
├── 00_request.md
├── 01_project_brief.md
├── 02_codex.json
├── 03_outline.json
├── chapters/chapter_XX/{00_summary.md,01_beats.json,02_draft.md,03_summary_after.md}
├── manuscript/{draft_full.md,final.md}
├── run_records/{step_manifest.jsonl,rendered_prompts/}
└── writing_log.md
```

## Operating Modes

- `full_auto`: run end to end without user pauses. Use for smoke tests and unattended acceptance runs.
- `milestone_review`: pause after project brief, after Codex/outline, and after chapter 1 draft so the user can correct direction.

For normal user-facing writing, prefer `milestone_review`. For automated tests, use `full_auto` unless testing checkpoints.

## Context Rules

- Treat Codex as stable story memory.
- Include `Global Codex` entries (`always_include: true`) in major generation prompts.
- Include `Relevant Codex` entries by `required_codex`, exact name/alias matches in the current chapter summary or beat, and manual additional context.
- Do not copy NovelCrafter `include(...)` syntax. Use platform-neutral context slots such as `relevant_codex`, `selected_context`, `role_prompt`, `additional_context`.
- Always validate beats before writing prose.

## When Implementing Or Testing

Read these files as needed:

- `core_spec/workflow.md` for step order.
- `core_spec/context_policy.md` for context assembly rules.
- `core_spec/runtime_contract.yaml` for read/write contracts.
- `core_spec/prompts/` for prompt templates.
- `core_spec/schemas/` for JSON output schemas.
- `references/quality_rubric_v1.md` for the fixed chapter-review value system when evaluating prose quality.

Use `scripts/run_acceptance.py` to run a test case with trace records. It supports DeepSeek through `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, and `DEEPSEEK_MODEL`.

## V1 Chapter Revision Mode

Use the V1 revision loop to compare direct write, simple engineered, full skill unrevised, and full skill revised outputs:

```bash
python3 longform-writing/scripts/run_v1_revision_loop.py --cases 05_medium_length_single_protagonist 10_mystery_clue_fairness_smoke 07_dual_timeline_continuity --max-iterations 3
```

The V1 goal is real-text blind quality, not workflow traceability. `full_revised` must beat both `direct_write` and `full_unrevised` in the required blind rankings.

## Acceptance Standard

A run passes V0 only if:

- required files exist and JSON parses
- prose is generated after beats and validation
- chapter 2+ prompts include prior `03_summary_after.md` as story so far
- rendered prompts and `step_manifest.jsonl` exist
- final manuscript is assembled from chapter drafts
- milestone-review runs record checkpoints and feedback application

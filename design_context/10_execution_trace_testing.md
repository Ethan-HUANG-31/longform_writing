# Execution Trace Testing

V0 tests must check both final manuscript quality and workflow execution correctness.

This trace is not an SFT trajectory export. It is a lightweight audit record that proves the skill followed the intended workflow and assembled prompts from the right context.

## Required Trace Artifacts

Each writing project should include:

```text
run_records/
├── step_manifest.jsonl
└── rendered_prompts/
    ├── 001_parse_request.md
    ├── 002_build_project_brief.md
    ├── 003_build_codex.md
    ├── 004_generate_outline.md
    ├── 005_chapter_01_summary.md
    ├── 006_chapter_01_beats.md
    ├── 007_chapter_01_validate_beats.md
    ├── 008_chapter_01_write_prose.md
    └── ...
```

## Step Manifest Schema

Each line in `step_manifest.jsonl` should be one JSON object:

```json
{
  "step_id": "008_chapter_01_write_prose",
  "workflow_step": "write_beat_prose",
  "prompt_template": "core_spec/prompts/08_write_beat_prose.md",
  "input_files": [
    "01_project_brief.md",
    "02_codex.json",
    "chapters/chapter_01/00_summary.md",
    "chapters/chapter_01/01_beats.json"
  ],
  "context_sections": [
    "Project Brief",
    "Relevant Codex",
    "Story So Far",
    "Current Chapter Summary",
    "Text Before",
    "Current Beat"
  ],
  "rendered_prompt": "run_records/rendered_prompts/008_chapter_01_write_prose.md",
  "output_files": [
    "chapters/chapter_01/02_draft.md"
  ],
  "status": "success"
}
```

## Prompt Assembly Checks

Tests should inspect rendered prompts, especially for beat-to-prose:

- It must include project brief or global constraints.
- It must include relevant Codex, or full Codex only when Codex is small.
- It must include previous chapter summaries when writing chapter 2 or later.
- It must include current chapter summary.
- It must include current text before the current beat.
- It must include the current beat.
- It must not include future chapter summaries.
- It must not include unrelated hidden solution notes.

## Workflow Order Checks

The trace must prove this order:

```text
request -> brief -> codex -> outline -> chapter summary -> beats -> validation -> prose -> summary_after -> merge
```

Required rules:

- Prose cannot be generated before beats.
- Prose cannot be generated before beat validation.
- Chapter 2+ prose must have access to earlier `03_summary_after.md`.
- `manuscript/draft_full.md` must be produced from chapter drafts, not directly from the original request.

## Test Case Design Principle

Use low-complexity stories for V0 testing:

- single protagonist
- simple supporting characters only when needed
- names like 小帅, 小美, 阿强
- one central object or rule
- three chapters
- one main reveal
- no seven-person ensemble
- no complex multi-POV structure

This keeps failures attributable to workflow or prompt assembly rather than story complexity.


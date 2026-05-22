# Writing Project V0 Directory

Each writing task should create a new project directory. The user should not manually paste files into a prebuilt directory.

Recommended runtime layout:

```text
runs/{project_slug}/
├── 00_request.md
├── 01_project_brief.md
├── 02_codex.json
├── 03_outline.json
├── chapters/
│   ├── chapter_01/
│   │   ├── 00_summary.md
│   │   ├── 01_beats.json
│   │   ├── 02_draft.md
│   │   └── 03_summary_after.md
│   ├── chapter_02/
│   │   ├── 00_summary.md
│   │   ├── 01_beats.json
│   │   ├── 02_draft.md
│   │   └── 03_summary_after.md
│   └── chapter_XX/
│       ├── 00_summary.md
│       ├── 01_beats.json
│       ├── 02_draft.md
│       └── 03_summary_after.md
├── manuscript/
│   ├── draft_full.md
│   └── final.md
├── run_records/
│   ├── step_manifest.jsonl
│   └── rendered_prompts/
└── writing_log.md
```

## File Roles

`00_request.md`
: Original user request. Do not overwrite.

`01_project_brief.md`
: Global creative contract: title, genre, premise, tone, POV, constraints, target length, prohibited elements.

`02_codex.json`
: Stable story facts. V0 stores entries with `global` or `relevant` inclusion scope. It should include global style/premise/rule entries, characters, locations, objects, and rules/lore. See `design_context/15_codex_design.md`.

`03_outline.json`
: Chapter-level plan. Each chapter should have `chapter_id`, `title`, and concrete `summary`.

`chapters/chapter_XX/00_summary.md`
: Writing plan for the current chapter, derived from the outline.

`chapters/chapter_XX/01_beats.json`
: Concrete beat list for the current chapter. Each beat should be executable and specific.

`chapters/chapter_XX/02_draft.md`
: Chapter prose generated from beats.

`chapters/chapter_XX/03_summary_after.md`
: Factual summary of what actually happened in the written chapter. Used as future context.

`manuscript/draft_full.md`
: Concatenation of all chapter drafts.

`manuscript/final.md`
: V0 can copy `draft_full.md`. Later versions may revise before writing final.

`writing_log.md`
: Lightweight process log.

`run_records/step_manifest.jsonl`
: Lightweight execution trace. Each line records one workflow step, prompt template, input files, context sections, rendered prompt path, output files, and status.

`run_records/rendered_prompts/`
: Stores rendered prompt snapshots for audit and testing. This is required so tests can verify prompt assembly, not just final manuscript content.

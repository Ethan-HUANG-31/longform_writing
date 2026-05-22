# Skill V0 Directory

V0 should be one composite workflow skill, not a collection of small skills.

The skill is reusable and fixed. Each run creates a separate writing project directory.

Recommended platform-neutral structure:

```text
longform_writing_skill_v0/
├── core_spec/
│   ├── design.md
│   ├── workflow.md
│   ├── context_policy.md
│   ├── runtime_contract.yaml
│   ├── prompts/
│   │   ├── 01_parse_request.md
│   │   ├── 02_build_project_brief.md
│   │   ├── 03_build_codex.md
│   │   ├── 04_generate_outline.md
│   │   ├── 05_generate_chapter_summary.md
│   │   ├── 06_generate_scene_beats.md
│   │   ├── 07_validate_scene_beats.md
│   │   ├── 08_write_beat_prose.md
│   │   ├── 09_summarize_chapter.md
│   │   └── 10_merge_manuscript.md
│   └── schemas/
│       ├── codex.schema.json
│       ├── outline.schema.json
│       ├── scene_beats.schema.json
│       └── beat_validation.schema.json
├── adapters/
│   ├── codex/
│   │   ├── SKILL.md
│   │   └── AGENTS.md
│   └── claude_code/
│       ├── SKILL.md
│       └── CLAUDE.md
└── templates/
    └── writing_project_v0/
        ├── 00_request.md
        ├── 01_project_brief.md
        ├── 02_codex.json
        ├── 03_outline.json
        ├── chapters/
        ├── manuscript/
        ├── run_records/
        │   ├── step_manifest.jsonl
        │   └── rendered_prompts/
        └── writing_log.md
```

## Why Platform Neutral First

Codex and Claude Code can reuse most of the design logic, prompt templates, schemas, context policy, runtime contract, and project template. Their packaging details differ, so adapters should be generated after the core spec is stable.

## Prompt File Format

Every prompt file should use the same sections:

- Purpose
- Inputs
- Output
- Constraints
- Prompt Template
- Failure Cases

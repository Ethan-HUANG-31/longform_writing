# Context Policy V0

Do not pass the full project state to every step. Render prompts with explicit, auditable sections.

## Required Rendered Prompt Sections

Use these section names when relevant:

- `Role Prompt`
- `Default Instructions`
- `Project Brief`
- `Global Codex`
- `Relevant Codex`
- `Story So Far`
- `Current Chapter Summary`
- `Text Before`
- `Current Beat`
- `Additional Instructions`
- `Additional Context`

## Codex Inclusion

`Global Codex`:

- entries with `always_include: true`
- style, genre, hard constraints, premise, central rules

`Relevant Codex`:

- entries in `required_codex`
- exact name/alias matches in chapter summary or beat
- manually supplied additional context

If Codex is small, full minimal Codex is acceptable, but the rendered prompt should still label global vs relevant sections.

## Step Context

`generate_outline`:

- request
- project brief
- global Codex
- relevant protagonist/setting Codex

`generate_scene_beats`:

- project brief
- global Codex
- current chapter summary
- previous summary_after if available
- relevant Codex

`write_beat_prose`:

- project brief
- global Codex
- relevant Codex
- previous chapter summaries as story so far
- current chapter summary
- text before
- current beat

`summarize_chapter`:

- chapter draft only, plus brief instruction to summarize factual events.

Never include future chapter summaries in prose prompts unless the current step explicitly requires the reveal.


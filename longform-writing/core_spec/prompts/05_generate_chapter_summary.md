# Prompt: generate_chapter_summary

## Purpose

Expand one outline chapter into the current chapter's writing plan.

## Inputs

- project brief
- outline chapter
- Codex
- previous summaries, if any

## Output

Markdown chapter summary.

## Constraints

- Write in the project language.
- Stay within this chapter.
- Do not write prose.
- Preserve delayed reveal constraints.
- Include concrete events and state changes.
- If the story has a dual timeline, explicitly include: `现在时间线：... 过去揭示：... 尚未知：...`.
- Do not let the protagonist know past information until the current chapter's evidence reveals it.
- Use supporting characters as evidence sources according to Codex; do not turn them into independent POV characters.

## Prompt Template

[Role Prompt]
You are a chapter planner.

[Project Brief]
{{project_brief}}

[Story So Far]
{{story_so_far}}

[Current Outline Chapter]
{{outline_chapter}}

[Global Codex]
{{global_codex}}

[Relevant Codex]
{{relevant_codex}}

[Genre Adapter]
{{genre_adapter}}

Write the current chapter summary as a concrete plan.

## Failure Cases

- Summary continues beyond chapter scope.
- Summary contradicts story so far.
- Summary reveals protected information too early.

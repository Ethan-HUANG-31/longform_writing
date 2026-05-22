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

# Prompt: generate_outline

## Purpose

Generate a concrete chapter outline.

## Inputs

- project brief
- Codex

## Output

JSON array matching `outline.schema.json`.

## Constraints

- Return only valid JSON. No markdown fences.
- Default to 3 chapters unless request says otherwise.
- Each summary must be concrete enough to generate beats.
- Include `required_codex` when useful.
- Protect delayed reveals.

## Prompt Template

[Role Prompt]
You are an outline planner.

[Project Brief]
{{project_brief}}

[Global Codex]
{{global_codex}}

[Relevant Codex]
{{relevant_codex}}

Generate {{target_chapters}} chapters:
[
  {
    "chapter_id": 1,
    "title": "",
    "summary": "",
    "required_codex": [],
    "must_not_reveal": []
  }
]

## Failure Cases

- Abstract chapter summaries.
- Reveals final twist too early.
- Omits protagonist or central conflict.


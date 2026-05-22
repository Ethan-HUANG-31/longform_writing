# Prompt: build_project_brief

## Purpose

Create the global creative contract for the writing project.

## Inputs

- raw request
- parsed requirement

## Output

Markdown project brief.

## Constraints

- Be concrete and concise.
- Preserve forbidden elements.
- State default assumptions.
- Do not write story prose.

## Prompt Template

[Role Prompt]
You are a story planner preparing a project brief for a structured longform fiction workflow.

[Default Instructions]
Use the request as source of truth. Make the smallest reasonable assumptions. Do not add unsupported complexity.

[User Request]
{{user_request}}

[Parsed Requirement]
{{parsed_requirement}}

[Genre Adapter]
{{genre_adapter}}

Write `01_project_brief.md` with sections:
- Title
- Language
- Genre
- Target Scale
- Premise
- Protagonist
- Supporting Characters
- Setting
- Tone
- POV
- Style Constraints
- Prohibited Elements
- Must Include
- Must Not Reveal Early
- Automation Mode
- Default Assumptions

## Failure Cases

- Brief contradicts the request.
- Brief introduces multiple protagonists in V0.
- Brief omits hard constraints.

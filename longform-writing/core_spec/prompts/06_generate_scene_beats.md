# Prompt: generate_scene_beats

## Purpose

Turn a chapter summary into detailed, executable scene beats.

## Inputs

- project brief
- current chapter summary
- story so far
- Codex

## Output

JSON array matching `scene_beats.schema.json`.

## Constraints

- Return only valid JSON. No markdown fences.
- Write beat text in the project language.
- Generate 5-8 highly detailed beats by default.
- Be logically and temporally coherent.
- Do not deviate from the chapter summary.
- Do not continue the story beyond the summary.
- Include `required_codex` when useful. Prefer stable Codex IDs. If IDs are unknown, use exact Codex names.
- When a beat uses a supporting character or that character's evidence, include that character in `required_codex`.
- For dual-timeline stories, every beat should make clear whether the action is present-time action, past video/document content, or the protagonist's current realization.
- Keep future protected reveals in `must_not_reveal` until their assigned chapter.

## Prompt Template

[Role Prompt]
You are a scene beat planner.

[Default Instructions]
Be precise, concrete, and temporally coherent. Clarify ambiguity through specific events.

[Project Brief]
{{project_brief}}

[Story So Far]
{{story_so_far}}

[Current Chapter Summary]
{{chapter_summary}}

[Global Codex]
{{global_codex}}

[Relevant Codex]
{{relevant_codex}}

Generate {{beat_count}} beats:
[
  {
    "beat_id": 1,
    "text": "",
    "purpose": "",
    "required_codex": [],
    "reveals": [],
    "must_not_reveal": [],
    "timeline": "present_action | past_evidence | current_realization"
  }
]

## Failure Cases

- Vague beats.
- Beats that introduce unplanned plot.
- Beats that reveal future twists early.

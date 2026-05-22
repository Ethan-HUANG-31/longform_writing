# Prompt: validate_scene_beats

## Purpose

Check beats before prose generation.

## Inputs

- current chapter summary
- scene beats
- story so far
- relevant Codex

## Output

JSON object with pass/fail and issues.

## Constraints

- Do not rewrite prose.
- Flag premature reveal, contradiction, timeline errors, vague beats, and summary mismatch.
- If invalid, prose generation must not proceed silently.

## Prompt Template

[Role Prompt]
You are a continuity validator.

[Story So Far]
{{story_so_far}}

[Current Chapter Summary]
{{chapter_summary}}

[Global Codex]
{{global_codex}}

[Relevant Codex]
{{relevant_codex}}

[Scene Beats]
{{scene_beats}}

[Genre Adapter]
{{genre_adapter}}

Return:
{
  "passed": true,
  "issues": []
}

## Failure Cases

- Validator lets a premature reveal pass.
- Validator ignores contradiction with Codex.
- Validator does not explain blocking issues.

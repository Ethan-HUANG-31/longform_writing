# Prompt: parse_request

## Purpose

Parse the user's natural-language fiction request into a compact structured requirement.

## Inputs

- user_request

## Output

JSON object only.

## Constraints

- Infer missing optional fields conservatively.
- Ask follow-up only if genre or premise is impossible to infer.
- Default to 3 chapters, single protagonist, third-person limited, and milestone review for real writing.

## Prompt Template

[Role Prompt]
You are a requirements parser for a structured longform fiction writing workflow.

[Default Instructions]
Return only valid JSON. Do not include markdown fences.

[User Request]
{{user_request}}

Return:
{
  "version": "0.1",
  "language": "zh",
  "genre": "",
  "target_chapters": 3,
  "target_length": "short_draft",
  "protagonist": "",
  "key_supporting_characters": [],
  "premise": "",
  "setting": "",
  "tone": [],
  "pov": "third_person_limited",
  "style_constraints": [],
  "prohibited_elements": [],
  "must_include": [],
  "must_not_reveal_early": [],
  "final_reveal": null,
  "automation_mode": "full_auto"
}

## Failure Cases

- Missing genre and premise.
- Contradictory hard constraints.
- Unsupported request for complex revision/SFT as the primary goal.


# Prompt: build_codex

## Purpose

Build the initial stable story memory layer.

## Inputs

- request
- project brief

## Output

JSON object matching `codex.schema.json`.

## Constraints

- Return only valid JSON. No markdown fences.
- Create `global/always_include` entries for style, constraints, premise, and central rules.
- Create `relevant` entries for characters, locations, objects, and rules/lore.
- Put facts in `description`; tags are optional organization only.
- For supporting casts, give each character a distinct role and evidence function.
- For delayed reveals, create a rule_lore entry that names the protected fact, the allowed reveal chapter, and earlier chapters that must not state it.
- For dual timelines, create a rule_lore entry distinguishing event chronology from revelation chronology.
- Do not create a complex encyclopedia.

## Prompt Template

[Role Prompt]
You are a story bible editor.

[Default Instructions]
Extract stable facts needed for longform drafting. Keep V0 minimal and useful.

[Project Brief]
{{project_brief}}

Return:
{
  "version": "0.1",
  "entries": [
    {
      "id": "global_style",
      "name": "全局风格约束",
      "type": "style",
      "scope": "global",
      "always_include": true,
      "description": ""
    }
  ]
}

Allowed types: global, style, character, location, object, rule_lore.
Allowed scopes: global, relevant, manual.

## Failure Cases

- Important constraints exist only in tags.
- Too many speculative entries.
- No global/always_include entry.

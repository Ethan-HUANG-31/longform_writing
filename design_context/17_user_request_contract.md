# User Request Contract V0

This document defines what the user should provide when invoking `longform_writing_skill_v0`.

The skill should accept natural language, but internally convert it into a structured request before writing.

## Design Principle

Do not require the user to fill a long form.

V0 should work from a concise writing request, then make reasonable defaults. It should ask follow-up questions only when the missing or contradictory information would make the task impossible or likely to fail.

## Minimal User Request

The minimum useful request should include:

1. Story type or genre
2. Target scale
3. Core premise
4. Important constraints or forbidden elements

Example:

```text
写一个 3 章左右的密室心理惊悚短篇。主角叫小帅，旧同事叫小美。小帅被困在选择室里，被迫重新面对三年前一次让自己获益、却伤害小美的项目选择。不要血腥、肢体伤害或超自然解释，风格冷静克制。
```

This is enough for V0.

## Recommended User Request Fields

The request can include these fields in natural language:

| Field | Required | Default if missing |
| --- | --- | --- |
| language | no | inherit user request language |
| genre | yes | ask if absent |
| target_chapters | no | 3 chapters |
| target_length | no | short draft |
| protagonist | no | generate simple name such as 小帅 |
| key_supporting_character | no | generate simple name such as 小美 if needed |
| premise | yes | ask if absent |
| setting | no | infer from premise |
| tone | no | infer from genre |
| pov | no | third-person limited |
| tense | no | present tense for summaries; prose follows language/style default |
| style_constraints | no | derive from genre and request |
| prohibited_elements | no | no gore, no explicit bodily harm, no supernatural unless requested |
| must_include | no | empty |
| must_not_reveal_early | no | infer from twist/reveal if present |
| final_reveal | no | optional; can be generated if absent |
| user_checkpoints | no | fully automatic unless user asks for confirmation |

## Parsed Requirement Schema

The first step should create an internal parsed requirement object.

Recommended shape:

```json
{
  "version": "0.1",
  "language": "zh",
  "genre": "密室心理惊悚",
  "target_chapters": 3,
  "target_length": "short_draft",
  "protagonist": "小帅",
  "key_supporting_characters": ["小美"],
  "premise": "小帅被困在选择室里，被迫重新面对三年前一次让自己获益、却伤害小美的项目选择。",
  "setting": "选择室",
  "tone": ["冷静", "克制", "压抑"],
  "pov": "third_person_limited",
  "style_constraints": [
    "show don't tell",
    "dialogue and concrete action should advance the scene",
    "avoid abstract pressure descriptions when concrete details can carry tension"
  ],
  "prohibited_elements": [
    "血腥",
    "肢体伤害",
    "超自然解释"
  ],
  "must_include": [
    "选择规则",
    "旧案真相",
    "道德反转"
  ],
  "must_not_reveal_early": [
    "最终道德反转"
  ],
  "final_reveal": null,
  "automation_mode": "milestone_review"
}
```

V0 can write this into the top of `01_project_brief.md` or a future `00_parsed_requirement.json`. To keep the runtime directory minimal, V0 may skip a standalone parsed JSON file if `01_project_brief.md` contains the parsed fields clearly.

## When To Ask Follow-Up Questions

Ask a follow-up before starting only when:

- genre is absent and cannot be inferred
- premise is absent or too vague
- requested scale is too large for V0
- requirements conflict, such as "no supernatural" and "ghost is the murderer"
- the user requests V0-excluded features as the main goal, such as complex revision, SFT export, or multi-agent writing
- prohibited content or safety boundaries are unclear in a way that affects generation

Do not ask just because optional details are missing.

## Default Assumptions

If the user gives a normal short fiction request, V0 should assume:

- 3 chapters
- single protagonist
- simple supporting cast
- third-person limited
- one main object/rule/reveal
- concise complete first draft
- no complex subplot tracking
- no revision loop
- milestone review for real user-facing writing

For acceptance tests and unattended runs, use `full_auto`.

## User-Facing Prompt Template

When asking the user for a writing request, use a lightweight prompt:

```text
请给我一个写作需求。最少包含：题材、篇幅/章节数、核心设定、不能出现的内容。

例如：
写一个 3 章密室心理惊悚短篇。主角叫小帅，旧同事叫小美。小帅醒在选择室里，被迫重新面对三年前一次项目选择。不要血腥、肢体伤害或超自然解释，风格冷静克制。
```

## What The Skill Should Not Require

Do not require the user to provide:

- full outline
- full Codex
- all character profiles
- all chapter summaries
- beat list
- exact ending
- detailed style guide

The skill should generate these as intermediate artifacts unless the user supplies them.

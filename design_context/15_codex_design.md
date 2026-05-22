# Codex Design V0

This document defines the V0 Codex model and context inclusion rules for `longform_writing_skill_v0`.

V0 should borrow NovelCrafter's Codex idea, not its full implementation.

## Design Goal

Codex is the stable story memory layer.

It should store reusable facts that should not be reinvented during drafting:

- global story premise and rules
- style and genre constraints
- characters
- locations
- objects
- rules/lore

Codex should help context selection, but V0 should avoid complex automatic retrieval.

## Two Inclusion Modes

V0 Codex entries use two main inclusion modes.

### 1. Global / Always Include

These entries are included in every major generation prompt.

Use for:

- genre
- tone
- style guide
- hard constraints
- forbidden elements
- central premise
- central story rule
- global writing principles

NovelCrafter analogy: global entry / always include Codex entry.

V0 equivalent:

```json
{
  "id": "global_style",
  "name": "全局风格约束",
  "type": "style",
  "scope": "global",
  "always_include": true,
  "description": "冷静、克制、压抑；不使用血腥、肢体伤害或超自然解释；惊悚感来自规则、空间、倒计时和心理压力。"
}
```

### 2. Relevant / On Demand

These entries are included only when relevant to the current chapter, beat, or validation step.

Use for:

- protagonist
- supporting characters
- locations
- key objects
- local rules
- scene-specific lore

NovelCrafter analogy: entries retrieved because the scene/beat mentions them or because the user attaches them to scene context.

V0 equivalent:

```json
{
  "id": "character_xiaoshuai",
  "name": "小帅",
  "type": "character",
  "scope": "relevant",
  "always_include": false,
  "description": "28岁产品经理，习惯用逻辑合理化自己的选择。当前故事中是被审判者。",
  "aliases": ["小帅"]
}
```

## Recommended `02_codex.json` Shape

Use a simple grouped format for readability and validation:

```json
{
  "version": "0.1",
  "entries": [
    {
      "id": "global_style",
      "name": "全局风格约束",
      "type": "style",
      "scope": "global",
      "always_include": true,
      "description": "冷静、克制、压抑；不使用血腥、肢体伤害或超自然解释。"
    },
    {
      "id": "character_xiaoshuai",
      "name": "小帅",
      "type": "character",
      "scope": "relevant",
      "always_include": false,
      "description": "28岁产品经理，习惯用逻辑合理化自己的选择。"
    }
  ]
}
```

Allowed `type` values for V0:

- `global`
- `style`
- `character`
- `location`
- `object`
- `rule_lore`

Allowed `scope` values for V0:

- `global`
- `relevant`
- `manual`

Required fields:

- `id`
- `name`
- `type`
- `scope`
- `always_include`
- `description`

Optional fields:

- `aliases`
- `tags`
- `source`
- `first_mentioned_in`
- `notes`

Important: tags are for organization only. If the AI needs to know a fact, put it in `description`, not only in `tags`.

## Build Codex In V0

V0 should create Codex once near the start:

```text
00_request.md + 01_project_brief.md -> 02_codex.json
```

The `build_codex` step should create:

- 1-3 global/style entries
- protagonist entry
- key supporting character entries if requested
- main location entries
- central object entries
- central rule/lore entries

For the current smoke tests, Codex should include entries such as:

- 全局风格约束
- 小帅
- 小美
- 选择室
- 审判者
- 审判规则
- 蓝色钥匙, when relevant

## Automatic Extraction Policy

V0 should not attempt a full NovelCrafter-style automatic extraction system.

V0 should do only lightweight extraction:

1. During `build_codex`, infer obvious stable entities from the request and project brief.
2. During `generate_outline`, include `required_codex` names in each chapter object when useful.
3. During `generate_scene_beats`, include `required_codex` names in each beat object.
4. During context assembly, select relevant Codex by:
   - `required_codex` fields
   - exact name or alias match in current chapter summary
   - exact name or alias match in current beat
   - `always_include: true`
   - manual additional context

Do not build a complex entity extractor in V0.

Do not update Codex automatically after every chapter unless the workflow explicitly adds a future `update_codex` step.

## Context Inclusion Rules

### For Project Brief

No Codex needed. This step creates the global creative contract.

### For Build Codex

Read:

- `00_request.md`
- `01_project_brief.md`

Write:

- `02_codex.json`

### For Outline

Include:

- all global/always_include entries
- relevant protagonist and core setting entries
- full Codex if the Codex is still small

### For Chapter Summary

Include:

- all global/always_include entries
- entries named in the outline chapter
- previous summary_after if available

### For Scene Beats

Include:

- all global/always_include entries
- entries named in current chapter summary
- previous summary_after if available

Output beats should include `required_codex` when possible.

### For Beat Prose

Include:

- all global/always_include entries
- entries in current beat `required_codex`
- entries named in current beat text
- entries named in current chapter summary
- story_so_far from previous summaries
- current text_before

Do not include all Codex if the Codex grows large.

### For Beat Validation

Include:

- all global/always_include entries
- entries in current beat `required_codex`
- entries named in current chapter summary
- previous summaries

Validation should flag obvious conflicts between beat and Codex.

## Relevant Codex Rendering

Rendered prompt should expose both global and relevant parts:

```text
[Global Codex]
## Style
### 全局风格约束
Type: style
Description: 冷静、克制、压抑；不使用血腥、肢体伤害或超自然解释。

[Relevant Codex]
## Characters
### 小帅
Type: character
Description: 28岁产品经理，习惯用逻辑合理化自己的选择。

## Locations
### 选择室
Type: location
Description: 白色密闭房间，有金属桌、嵌入式屏幕、扬声器和无法打开的门。
```

`run_records/step_manifest.jsonl` should record whether the step used:

- `Global Codex`
- `Relevant Codex`
- `Full Codex`

## What To Defer To V1

- automatic Codex update after each chapter
- fuzzy semantic retrieval
- vector search
- separate detail fields like secrets, relationships, timeline, voice
- complex tags and hierarchy
- always include per scene group
- Codex conflict resolution UI

V0 only needs enough Codex structure to make context assembly auditable and reliable.


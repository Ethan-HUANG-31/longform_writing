# NovelCrafter Macro Mapping

This document defines how to translate NovelCrafter `include("Novelcrafter/...")` macros into platform-neutral context slots for `longform_writing_skill_v0`.

V0 should not replicate NovelCrafter's internal macro system. Exact macro expansion is unknown and not required. Implement equivalent context slots instead.

## Core Rule

Do not copy NovelCrafter macro syntax into our skill.

Use explicit, auditable slots:

- `{{relevant_codex}}`
- `{{selected_context}}`
- `{{default_instructions}}`
- `{{additional_instructions}}`
- `{{role_prompt}}`
- `{{additional_context}}`

These slots must appear in rendered prompt snapshots under `run_records/rendered_prompts/` when used.

## Macro Mapping

| NovelCrafter macro | Meaning | V0 context slot |
| --- | --- | --- |
| `Novelcrafter/Codex` | Codex context available to the current task, including always-include entries, task-relevant entries, and manually attached context | `{{relevant_codex}}` plus optional `{{global_codex}}` |
| `Novelcrafter/Chat/DefaultContext` | Currently selected chat/workshop context such as outline, chapters, scenes, snippets, and Codex entries | `{{selected_context}}` |
| `Novelcrafter/Chat/DefaultInstructions` | Default workshop/chat behavior rules | `{{default_instructions}}` |
| `Novelcrafter/AdditionalInstructions` | User or preset instructions added to the current prompt call | `{{additional_instructions}}` |
| `Novelcrafter/Personas` | Role/persona prompt such as writer, editor, planner, summarizer | `{{role_prompt}}` |
| `Novelcrafter/AdditionalContext` | User-provided extra context attached to this generation | `{{additional_context}}` |

## Relevant Codex Slot

Treat `Novelcrafter/Codex` as a formatted context block named `[Relevant Codex]`.

V0 selection rules:

1. Always include global style/genre constraints when available.
2. Include entries explicitly mentioned in the current beat.
3. Include entries explicitly mentioned in the current chapter summary.
4. Include entries manually passed through `additional_context`.
5. If Codex is small and relevance is ambiguous, include the full minimal Codex.
6. Do not include unrelated entries just because they exist.

See `design_context/15_codex_design.md` for the full Codex schema and inclusion rules.

Recommended format:

```text
[Relevant Codex]

## Characters
### 小帅
Type: Character
Description: 28岁产品经理，习惯用逻辑合理化自己的选择。当前故事中是被审判者。

### 审判者
Type: Character
Description: 不可见的幕后声音，通过扬声器、屏幕和录像向小帅提出旧案审判。

## Locations
### 选择室
Type: Location
Description: 白色密闭房间，有金属桌、空椅子、嵌入式屏幕、扬声器、监控红灯和无法打开的金属门。

## Rules / Lore
### 审判规则
Type: Lore
Description: 每轮审判都会重现一次旧案选择，小帅必须在倒计时内做出二选一决定。

## Style / Global
Description: 冷静、克制、压抑，不使用血腥或超自然解释。
```

Codex entry rules:

- Include name, type, scope, and description when available.
- Group entries by type.
- Do not rely on tags to convey story facts.
- Include tags only if they contain information not already represented in description.
- If a beat conflicts with attached Codex, validation should flag the contradiction before prose generation.

## Selected Context Slot

Treat `Novelcrafter/Chat/DefaultContext` as `[Selected Context]`.

V0 selected context is step-specific and defined by `context_policy.md`.

Default mapping:

```text
generate_outline:
- 00_request.md
- 01_project_brief.md
- 02_codex.json

generate_scene_beats:
- 01_project_brief.md
- 02_codex.json
- current chapter 00_summary.md
- previous chapter 03_summary_after.md if available

write_beat_prose:
- 01_project_brief.md
- relevant_codex
- story_so_far from previous summaries
- current chapter 00_summary.md
- current chapter text_before
- current beat
```

## Default Instructions Slot

Treat `Novelcrafter/Chat/DefaultInstructions` as `[Default Instructions]`.

Use this V0 instruction block:

```text
You are assisting with a structured longform fiction writing workflow.
Use the provided context as the source of truth.
Do not contradict the project brief, codex, chapter summary, or previous chapter summaries.
Do not reveal future plot information unless the current step requires it.
Return only the requested output format.
If the input is insufficient, make the smallest reasonable assumption and keep it consistent with the existing project files.
```

For Chinese writing tasks, this can be rendered in Chinese:

```text
你正在执行一个结构化长程小说写作流程。
请把提供的 project brief、codex、chapter summary、previous summaries 作为事实来源。
不要擅自改写设定，不要提前揭示后续反转。
只输出当前步骤要求的格式。
如果输入信息不足，做最小合理假设，并保持与已有项目文件一致。
```

## Role Prompt Slot

Treat `Novelcrafter/Personas` as `[Role Prompt]`.

V0 does not need a complex persona system. Use simple role prompts:

| Step | Role |
| --- | --- |
| `build_project_brief` | story planner |
| `build_codex` | story bible editor |
| `generate_outline` | outline planner |
| `generate_chapter_summary` | chapter planner |
| `generate_scene_beats` | scene beat planner |
| `validate_scene_beats` | continuity validator |
| `write_beat_prose` | fiction writer |
| `summarize_chapter` | factual summarizer |
| `merge_manuscript` | manuscript assembler |

## Additional Instructions Slot

Treat `Novelcrafter/AdditionalInstructions` as `[Additional Instructions]`.

Default: empty.

Use for temporary step-level requirements, such as:

```text
本章不要提前揭示审判者身份。
这一章加强小帅的产品经理式思维。
减少抽象压迫感描写。
```

## Additional Context Slot

Treat `Novelcrafter/AdditionalContext` as `[Additional Context]`.

Default: empty.

Use for manually supplied supporting material, such as:

```text
额外设定：选择室中的屏幕只播放旧案证据，不显示外部实时画面。
```

## Implementation Instruction For Codex

Use this instruction when creating prompt templates:

```text
Exact NovelCrafter macro expansion is unknown and not required for V0.
Implement approximate platform-neutral context slots:
relevant_codex, selected_context, default_instructions, role_prompt, additional_instructions, additional_context.
Do not copy NovelCrafter include syntax into the skill.
If later we obtain actual NovelCrafter prompt previews, refine slot formatting without changing the workflow contract.
```

# Prompt Design Decisions From Official NovelCrafter Prompts

This file records portable decisions extracted from official NovelCrafter prompt examples supplied by the user.

Do not copy the official prompts verbatim into the skill. Recreate the mechanisms in our own prompt templates.

## Generate Scene Beats

V0 prompt should:

- ask for a configurable beat count
- generate highly detailed beats
- require logical and temporal coherence
- clarify ambiguities instead of leaving vague instructions
- stay inside the chapter summary
- avoid continuing beyond the summary
- produce machine-readable JSON instead of NovelCrafter's numbered list
- include fields that help downstream context selection

Recommended JSON item:

```json
{
  "beat_id": 1,
  "text": "具体、可执行的 beat 描述",
  "purpose": "这个 beat 推进了什么",
  "required_codex": ["小帅", "选择室"],
  "reveals": [],
  "must_not_reveal": []
}
```

`required_codex` is important because V0 uses it for lightweight Codex retrieval. Do not rely on hidden semantic retrieval.

## Write Beat Prose

V0 prompt should:

- assign an expert fiction writer role
- include project/style rules before dynamic context
- include relevant Codex
- include story so far from previous chapter summaries
- include current text before the beat
- include the current beat instruction
- include optional user additional context
- tell the model to continue the story rather than summarize
- tell the model not to conclude the scene unless the beat requires it
- tell the model not to foreshadow or write beyond the beat
- allow early stopping once the beat is fulfilled
- require active, concrete prose and dialogue that advances action
- use platform-neutral context slots instead of NovelCrafter `include(...)` macros

The rendered prompt should be auditable and expose these sections:

```text
[Project Brief]
[Style Rules]
[Relevant Codex]
[Story So Far]
[Current Chapter Summary]
[Text Before]
[Current Beat]
[Additional Context]
```

Slot mapping is defined in `design_context/14_novelcrafter_macro_mapping.md`.

## Summarize Chapter

V0 prompt should:

- summarize actual written prose, not the original plan
- write concise running text, not bullets
- avoid meta openings
- use third person and present tense
- name characters directly
- preserve key event sequence, time/location shifts, reveals, decisions, and state changes
- omit sensory detail, background activity, and mundane actions unless plot-relevant
- avoid critique and revision advice

## Validate Beats

V0 validation should borrow from the beat and developmental prompts, but stay lightweight.

Checks:

- each beat is concrete
- beats follow logical and temporal order
- beats stay within chapter summary
- beats do not continue beyond the planned chapter
- beats do not reveal future information early
- beats contain enough named references for Codex grounding
- beats can be expanded into prose without inventing missing plot logic

## Developmental Review

Developmental Editor is useful as a future review module, not a V0 drafting dependency.

Useful future dimensions:

- concept clarity
- premise conflict
- central dramatic question
- theme through choices
- beginning/middle/end
- escalating stakes
- scene purpose
- pacing
- POV consistency
- dialogue utility
- characterization through pressure choices

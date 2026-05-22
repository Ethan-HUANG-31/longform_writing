# Phase C: Dynamic Genre Prompt Routing

## Purpose

Phase C verifies whether the skill can assemble different writing prompts based on genre and task shape.

The current V0 writer prompt is mostly generic Chinese prose expansion. That is acceptable for the first runnable skill, but future versions need genre adapters so the writer can respond differently to romance, fantasy, mystery, psychological thriller, and other forms.

Phase C should validate prompt routing before adding the V1 chapter revision loop.

## Core Idea

Do not create a completely separate prompt for every genre.

Use composable prompt slots:

```text
base_writer_prompt
  + language_style_rules
  + genre_adapter
  + project_brief
  + global_codex
  + relevant_codex
  + story_so_far
  + chapter_summary
  + text_before
  + current_beat
  + additional_context
```

The dynamic part is `genre_adapter`.

## Required Adapter Slots

### Base Adapter

Always included.

Responsibilities:

- active prose
- concrete action and dialogue
- follow current beat
- do not conclude beyond the beat
- preserve project language and POV
- avoid future reveal leakage

### Psychological Thriller / Locked-Room Moral Trial

Use when the project involves moral trial, confinement, psychological pressure, or old-case judgment.

Checks:

- rules of the room or trial remain clear
- pressure comes from choices, evidence, and self-justification
- no gore or supernatural explanation unless requested
- reveal sequence escalates moral pressure

### Romance

Use when the request is primarily romantic relationship development.

Checks:

- both romantic leads have distinct desire/fear/flaw
- relationship milestones progress believably
- obstacles create emotional stakes
- dialogue uses subtext and shifting intimacy
- resolution is not rushed

### Fantasy

Use when the request includes magic, invented worlds, fantasy species, or supernatural systems.

Checks:

- magic/world rules are explicit in Codex
- limitations and costs are respected
- worldbuilding serves plot and character choices
- terminology is introduced naturally
- fantasy elements do not solve conflicts without setup

### Mystery / Clue Fairness

Use when the request centers on clues, suspects, hidden truth, investigation, or final deduction.

Checks:

- clues are planted before payoff
- red herrings do not contradict final truth
- protagonist's deductions use available evidence
- final reveal is fair, not arbitrary
- clue state is tracked in summaries

## Prompt Routing Contract

Each run should record the selected adapter in traceable form.

Recommended fields:

```json
{
  "workflow_step": "write_beat_prose",
  "genre_adapter": "romance",
  "context_sections": [
    "Base Fiction Rules",
    "Genre Adapter",
    "Project Brief",
    "Global Codex",
    "Relevant Codex",
    "Story So Far",
    "Current Chapter Summary",
    "Text Before",
    "Current Beat"
  ]
}
```

Rendered prompts should visibly contain:

```text
[Genre Adapter]
...
```

## Positive Routing Checks

For each genre testcase:

- rendered prose prompts include the expected genre adapter
- quality or validation prompts include the expected genre-specific checks
- Codex includes genre-specific rule entries when needed
- output follows the genre-specific constraints

## Negative Routing Checks

For each genre testcase:

- rendered prompts do not include unrelated adapters
- romance does not include fantasy magic-system instructions
- fantasy does not include romance black-moment requirements unless the story is explicitly fantasy romance
- mystery does not include locked-room moral-trial rules unless requested

## Required Test Cases

Phase C should introduce at least three cases:

```text
08_genre_romance_adapter_smoke.md
09_genre_fantasy_adapter_smoke.md
10_mystery_clue_fairness_smoke.md
```

These tests may initially fail against V0. Their purpose is to define the target behavior before implementing prompt routing.

## Acceptance Signals

A Phase C run passes only if:

- `parse_request` identifies the genre or adapter target
- the selected adapter is recorded in `step_manifest.jsonl`
- rendered prompts include the expected adapter and exclude unrelated adapters
- `02_codex.json` contains genre-specific rules where needed
- final prose respects the adapter's core constraints
- normal V0 trace requirements still pass

## Relationship To Text Quality Judge

The future V1 quality judge should use the same adapter selection.

Example:

```text
romance writer adapter -> romance quality rubric
fantasy writer adapter -> fantasy quality rubric
mystery writer adapter -> clue fairness quality rubric
```

The writer and judge should share genre metadata, but they should remain separate components.


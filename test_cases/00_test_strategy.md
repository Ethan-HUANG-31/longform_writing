# Test Strategy For Longform Writing Skill V0

## Core Principle

V0 tests should diagnose workflow reliability, not story ambition.

Use simple stories first:

- single protagonist
- names such as 小帅, 小美, 阿强
- three chapters
- one central object, room, or rule
- one delayed reveal
- no ensemble cast
- no complex multi-POV
- no seven-character moral web

The earlier seven-character setup is useful as a future stress test, not as the first smoke test.

## Phase Expansion

After the four core V0 smoke tests pass, expand validation in two phases.

## Control Baselines

Before claiming that the structured skill is useful, compare it with simpler baselines.

Use control baselines on selected harder cases:

```text
Control A: direct write
Control B: simple engineered write
Treatment: full longform-writing skill
```

The controls should be evaluated on:

- requirement fulfillment
- continuity
- reveal control
- structural coherence
- traceability
- revision readiness

The full skill does not need to beat direct writing on prose elegance every time. Its main value claim is stronger process control for longform writing.

Recommended comparison cases:

- `05_medium_length_single_protagonist`
- `07_dual_timeline_continuity`
- `10_mystery_clue_fairness_smoke`

### Phase B: Complexity Expansion

Phase B raises story complexity without adding new workflow features.

It checks whether the base workflow survives:

- 5-chapter continuity
- more supporting characters while preserving one protagonist
- dual timeline or staged reveals
- longer delayed-reveal chains

Phase B should still use the existing workflow and should not depend on a revision loop.

### Phase C: Dynamic Genre Prompt Routing

Phase C checks whether the skill can route genre-specific prompt instructions.

It should verify:

- expected genre adapter is selected
- rendered prompts include the expected adapter
- unrelated adapters are excluded
- genre-specific Codex rules are present when needed
- normal V0 trace checks still pass

Phase C test cases may initially fail before genre routing is implemented.

## What Tests Must Check

Tests must check two layers:

1. Final artifacts and story content.
2. Execution trace and prompt assembly.

The skill can fail even if the final prose looks acceptable, because V0's purpose is to verify a reusable writing workflow.

## Required Runtime Records

Each test run should produce:

- `run_records/step_manifest.jsonl`
- `run_records/rendered_prompts/*.md`

The manifest proves which workflow steps ran. Rendered prompts prove context was assembled correctly.

## Static Checks

- Required files exist.
- JSON files parse.
- Chapters in `03_outline.json` match chapter folders.
- Each chapter has summary, beats, draft, and summary after.
- `manuscript/draft_full.md` includes chapter drafts.
- `manuscript/final.md` exists.

## Trace Checks

- Step order follows the workflow.
- Prose generation occurs after beat validation.
- Chapter 2+ prompts include previous summaries as story so far.
- Prompt templates listed in the manifest exist.
- Rendered prompt files listed in the manifest exist.
- Output files listed in the manifest exist after successful steps.

## Prompt Assembly Checks

For beat-to-prose:

- includes project brief
- includes relevant Codex
- includes story so far for chapter 2+
- includes current chapter summary
- includes current beat
- includes text before
- excludes future chapter summaries

For summarization:

- includes chapter draft
- asks for factual memory, not critique

For validation:

- includes chapter summary
- includes beats
- includes relevant Codex
- checks timeline, premature reveal, and summary alignment

## Content Checks

Keep content checks basic:

- story follows the requested protagonist and premise
- no forbidden content appears
- delayed reveal is not exposed early
- summary after records what happened
- later chapter uses earlier summary

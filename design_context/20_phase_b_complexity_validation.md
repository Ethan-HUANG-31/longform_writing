# Phase B: Complexity Expansion Validation

## Purpose

Phase B verifies whether the existing V0 writing workflow generalizes beyond the initial low-complexity smoke tests.

This phase should not introduce revision loops or genre-specific prompt adapters yet. It raises task complexity while keeping the same core workflow:

```text
request -> brief -> codex -> outline -> chapter summary -> beats -> validation -> prose -> summary_after -> merge
```

The goal is to discover whether the V0 workflow breaks when the story has more chapters, more supporting characters, more timeline pressure, or more continuity requirements.

## Boundary

Phase B is still a writing-skill validation phase, not an SFT trajectory-quality phase.

It checks whether the generated writing project remains usable:

- project artifacts are complete
- context assembly remains correct
- Codex selection remains grounded
- `summary_after` supports later chapters
- delayed reveal boundaries are preserved
- final manuscript fulfills required story promises

It does not judge whether the agent trajectory is valuable training data.

## Why This Phase Comes Before V1 Revision Loop

The revision loop should not be added until the base writer can handle moderately harder requests.

If revision is added too early, failures become hard to attribute:

```text
Was the story weak because:
- the base writer could not plan the task?
- genre prompt routing was wrong?
- the reviewer gave poor feedback?
- the reviser damaged the chapter?
```

Phase B isolates the base workflow's generalization limits.

## Complexity Axes

### 1. Longer Continuity

Move from 3 chapters to 5 chapters.

Checks:

- chapter 4 and 5 prompts include earlier `summary_after` context
- earlier facts are not forgotten
- delayed reveal is not exposed before the requested chapter
- final reveal is actually written, not only planned

### 2. Supporting Cast Without Ensemble Drift

Add 3-4 supporting characters while keeping one protagonist.

Checks:

- protagonist remains the only main viewpoint
- supporting characters do not become equal protagonists
- Codex contains the supporting characters
- relevant Codex is selected when a supporting character appears
- character roles remain stable

### 3. Dual Timeline

Use a present-time line and a past-time line.

Checks:

- chapter summaries distinguish present events from past memories
- beats do not confuse what the protagonist currently knows
- past information is revealed only when the present-time trigger occurs
- `summary_after` records both event time and revelation time

### 4. Multi-Step Reveal

Require a reveal to be split across chapters.

Checks:

- each chapter reveals only its assigned part
- intermediate clues are remembered later
- final chapter assembles the truth
- early prose prompts do not leak final answer

## Required Test Cases

Phase B should introduce at least three cases:

```text
05_medium_length_single_protagonist.md
06_supporting_cast_codex_routing.md
07_dual_timeline_continuity.md
```

These tests should run against the V0 workflow before Phase C or V1 revision work starts.

## Acceptance Signals

A Phase B run passes only if:

- required artifacts exist
- manifest and rendered prompts are complete
- all successful model steps reference existing prompt templates
- prose generation follows beat validation
- chapter 2+ prompts include prior summaries
- final manuscript fulfills explicit delayed-reveal requirements
- content remains within user constraints
- the story does not collapse into an unintended ensemble or unrelated subplot

## Failure Categories

### Writer Failure

The workflow is traceable, but the story misses required content.

Examples:

- final reveal planned but absent from prose
- supporting character role changes mid-story
- chapter 5 ignores chapter 2 evidence

### Context Failure

The rendered prompt does not contain the needed context.

Examples:

- chapter 4 prompt omits chapter 1 `summary_after`
- relevant character Codex is absent from a beat involving that character
- dual-timeline state is not present in summary context

### Spec Failure

The testcase is too ambiguous or impossible to judge.

Examples:

- reveal timing is not specified clearly
- supporting character count conflicts with "single protagonist"
- acceptance check requires literary quality without observable criteria


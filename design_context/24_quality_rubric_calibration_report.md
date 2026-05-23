# Phase D0: Quality Rubric Calibration Report

## Purpose

Phase D0 fixes the value system for the future chapter review / revision loop.

This phase does **not** implement the revision loop and does **not** allow the judge to evolve its own rubric. It only defines and calibrates a fixed V1 evaluation rubric so V1 can review chapters with a stable value system.

## Delivered Artifacts

- `longform-writing/references/quality_rubric_v1.md`
  - fixed V1 literary-quality and workflow-control rubric;
  - 1-5 score anchors;
  - evidence, issue, revision-target requirements;
  - blocking rules;
  - required JSON output shape.
- `longform-writing/core_spec/schemas/chapter_review.schema.json`
  - machine-checkable schema draft for future `chapter_review` output.
- `longform-writing/scripts/run_quality_calibration.py`
  - calibration runner for existing direct/simple/full-skill samples;
  - supports `heuristic` mode for local no-upload calibration;
  - supports `deepseek` mode only when external upload is explicitly approved.

## Fixed V1 Rubric

The rubric is derived from `NovelCrafter Developmental Editor 写作评价准则拆解.md`, but it is not copied verbatim. The source document is human-editor advice; V1 converts it into LLM-judge-friendly scoring.

V1 separates two conclusions.

### Literary Quality

1. Story Foundation
2. Narrative Arc
3. Structural Progression
4. Pacing
5. Characterization
6. Dialogue
7. POV / Narrative Distance
8. Genre Fulfillment

These dimensions answer:

```text
Does the chapter/manuscript work as fiction?
```

### Workflow Control

1. Beat Fidelity
2. Continuity
3. Reveal Control
4. Codex Grounding
5. Revision Safety

These dimensions answer:

```text
Can the system safely revise this chapter without breaking longform constraints?
```

The distinction is important: a direct-write manuscript can be readable while still failing reveal control or revision traceability.

## Calibration Run

The calibration used existing samples:

```text
05_medium_length_single_protagonist
07_dual_timeline_continuity
10_mystery_clue_fairness_smoke
```

For each case, it compared:

```text
direct_write
simple_engineered
full_skill
```

The first attempted `deepseek` run was blocked by policy because it would upload local sample manuscripts and context to a third-party API. To avoid data exfiltration, the completed calibration used local `heuristic` mode against existing baseline/full-skill reports and manuscript markers.

Generated local calibration artifacts are under:

```text
quality_calibration_runs/
```

That directory is ignored by git.

## Heuristic Calibration Summary

| Case | Method | Literary | Control | Weighted | Revision Required | Blocking Issues |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| 05 | direct_write | 3.25 | 1.80 | 2.45 | true | 2 |
| 05 | simple_engineered | 2.88 | 2.20 | 2.51 | true | 0 |
| 05 | full_skill | 4.00 | 4.00 | 4.00 | false | 0 |
| 07 | direct_write | 3.12 | 1.80 | 2.39 | true | 2 |
| 07 | simple_engineered | 3.00 | 2.20 | 2.56 | true | 1 |
| 07 | full_skill | 4.00 | 4.00 | 4.00 | false | 0 |
| 10 | direct_write | 3.25 | 1.80 | 2.45 | true | 2 |
| 10 | simple_engineered | 3.00 | 2.20 | 2.56 | true | 1 |
| 10 | full_skill | 4.00 | 4.00 | 4.00 | false | 0 |

## Calibration Findings

### What Has Good Signal

Workflow-control dimensions have strong signal on current data:

- Reveal Control catches 05 direct-write early missing-cover reveal.
- Continuity catches 07 missing dual-timeline markers.
- Reveal Control / Continuity catch 10 clue-payoff failures.
- Revision Safety separates direct-write outputs from structured skill outputs because direct-write has no localizable artifacts.

These dimensions should be kept for V1 and treated as revision safety gates.

### What Is Still Weak

Literary-quality dimensions are directionally useful but not yet deeply validated:

- Heuristic mode can detect chapter count, length, dialogue punctuation, and known report failures.
- It cannot reliably judge subtle prose quality, dialogue subtext, character arc naturalness, or reader engagement.
- Therefore, V1 should not claim literary superiority from this heuristic calibration alone.

The fixed rubric is still useful because it gives the future LLM judge a stable shape, but literary-quality scores need a later LLM/human calibration pass.

### Rubric Decision

Keep all 8 literary dimensions and all 5 workflow-control dimensions for V1.

Do not merge literary and workflow dimensions. The current data shows the split is necessary:

```text
direct/simple can look readable while failing control;
full skill can pass control while still needing future prose-quality review.
```

## Blocking Rules For V1

Use the blocking rules from `quality_rubric_v1.md`:

- Any Workflow Control dimension with `score <= 2` is blocking.
- Reveal Control with `score <= 3` is blocking.
- POV / Narrative Distance with `score <= 2` is blocking.
- Any Literary Quality dimension with `score <= 2` is blocking if it prevents the chapter from fulfilling its story purpose.
- Overall weighted score below `3.5` requires revision unless all issues are explicitly non-actionable.

For V1 revision loop, the reviser should consume:

```text
blocking_issues
revision_target
must-preserve constraints
```

It should not revise from aggregate scores alone.

## Recommendation For V1 Revision Loop

Proceed to V1 revision-loop implementation with this fixed rubric, but keep the first V1 conservative:

```text
chapter draft
-> chapter_review.json using quality_rubric_v1
-> revision_plan from blocking issues and revision targets
-> local chapter revision
-> summary_after from revised draft
```

Do not implement rubric self-evolution in V1.

Record judge failures as evaluator-rule improvement signals for a later phase.

## External LLM Calibration Note

The `deepseek` calibration mode exists but was not run to completion in this phase because it would upload sample manuscripts and context to an external API.

To run it later, the user should explicitly approve that specific data upload after reviewing the risk. The local heuristic calibration is sufficient to define the V1 rubric shape and control gates, but not sufficient to prove nuanced literary-quality judgment.

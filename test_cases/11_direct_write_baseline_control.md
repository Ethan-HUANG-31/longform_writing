# Control Test 11: Direct Write Baseline

## Purpose

Measure how well a model performs when asked to write the full story directly from the user request, without structured intermediate artifacts.

This is a control baseline, not a skill workflow test.

## Baseline Method

Use one prompt:

```text
请根据下面的用户需求，直接写出完整小说。不要先输出大纲，不要解释过程，只输出正文。

<user_request>
...
</user_request>
```

## Recommended Source Requests

Run this baseline against:

- `05_medium_length_single_protagonist`
- `07_dual_timeline_continuity`
- `10_mystery_clue_fairness_smoke`

These cases contain continuity, reveal, or clue-fairness pressure that should expose the limits of direct writing.

## Expected Artifacts

```text
baseline_runs/direct_write/<case_name>/
  request.md
  prompt.md
  manuscript.md
  baseline_report.md
```

## Checks

### Requirement Fulfillment

- Does the manuscript follow the requested premise?
- Does it use the requested characters?
- Does it respect forbidden content?
- Does it produce the requested number of chapters or a close equivalent?

### Continuity

- Are earlier facts remembered later?
- Do character roles remain stable?
- Does the timeline remain coherent?

### Reveal Control

- Does the manuscript reveal protected information too early?
- Does it fulfill the final reveal in prose?

### Traceability

- Since direct writing has only one prompt, report traceability as limited.
- If a failure occurs, note whether the failure can be localized to a specific planning step. Usually it cannot.

## Expected Weaknesses

Direct writing may have smoother prose, but it is expected to struggle with:

- staged reveal timing
- long continuity
- clue-state tracking
- targeted revision readiness
- failure localization

## Pass / Fail Use

This baseline should not be used to reject the full skill.

It should be used for comparison:

```text
If direct write passes a simple case, that means the case is not strong enough to justify the structured workflow.
If direct write fails a complex case that the full skill passes, that supports the workflow design.
```


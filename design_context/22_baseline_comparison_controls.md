# Baseline Comparison Controls

## Purpose

The longform-writing skill should not only prove that it can produce a manuscript. It should also prove that its structured workflow is worth the extra orchestration cost.

This document defines control baselines for comparison:

```text
Control A: direct write
Control B: simple engineered write
Treatment: full longform-writing skill
```

The comparison answers:

```text
Does the structured skill outperform simpler prompting on continuity, reveal control, Codex grounding, traceability, and revision readiness?
```

It does not need to prove literary superiority in every run. It should show that the structured workflow creates observable advantages on tasks where longform planning matters.

## Control A: Direct Write

The model receives the full user request and is asked to write the whole story directly.

Expected artifacts:

```text
baseline_runs/direct_write/
  request.md
  prompt.md
  manuscript.md
  baseline_report.md
```

Allowed context:

- only the original user request
- a simple instruction to write the full story

Not allowed:

- separate Codex
- outline file
- chapter summaries
- beat files
- story-so-far memory
- validation before prose

This control measures whether the model can solve the task without engineering.

## Control B: Simple Engineered Write

The model uses a minimal two-step or three-step structure:

```text
request
  -> outline
  -> write chapters from outline
  -> optional merge
```

Expected artifacts:

```text
baseline_runs/simple_engineered/
  request.md
  outline.md
  chapter_01.md
  chapter_02.md
  ...
  manuscript.md
  baseline_report.md
```

Allowed context:

- original request
- model-generated outline
- previous chapter text or a short rolling summary if explicitly included

Not allowed:

- full Codex system
- beat-level validation
- protected reveal redaction
- relevant/global Codex routing
- step manifest equivalent to the full skill

This control measures whether a lightweight writing pipeline is enough.

## Treatment: Full Skill

The full skill uses:

- project brief
- Codex
- outline
- chapter summaries
- scene beats
- beat validation
- beat-to-prose generation
- summary-after memory
- manifest and rendered prompt trace

This treatment is more expensive. It should be compared against controls on failure modes that the controls are expected to struggle with.

## Comparison Dimensions

### 1. Requirement Fulfillment

Checks:

- requested chapters or scale are respected
- required characters and objects appear
- forbidden content is absent
- final reveal or ending promise is fulfilled

### 2. Continuity

Checks:

- later chapters remember earlier facts
- character roles stay stable
- object states and clue states are preserved
- timeline remains coherent

### 3. Reveal Control

Checks:

- protected future information is not revealed early
- intermediate clues appear at the requested time
- final reveal is actually written in prose

### 4. Structural Coherence

Checks:

- each chapter has a distinct function
- chapters do not repeat the same scene pattern without change
- setup, complication, and resolution are visible

### 5. Traceability

Checks:

- can we inspect what prompt produced each artifact?
- can we identify where a failure entered?
- can we reproduce or patch a failed step?

Direct write is expected to score poorly here. That is acceptable and should be recorded.

### 6. Revision Readiness

Checks:

- does the run produce intermediate artifacts that a revision loop can target?
- can the system revise one chapter without rewriting the whole story?
- are constraints explicit enough for a reviser?

## Evaluation Format

Each comparison should produce a report:

```json
{
  "test_case": "05_medium_length_single_protagonist",
  "methods": {
    "direct_write": {
      "pass": false,
      "strengths": [],
      "failures": [
        {
          "dimension": "Reveal Control",
          "issue": "The missing cover warning appears in chapter 2.",
          "evidence": "..."
        }
      ]
    },
    "simple_engineered": {
      "pass": false,
      "strengths": [],
      "failures": []
    },
    "full_skill": {
      "pass": true,
      "strengths": [],
      "failures": []
    }
  },
  "conclusion": "The full skill is justified because it preserved delayed reveal and produced traceable intermediate artifacts."
}
```

## Recommended Comparison Cases

Use controls on tasks where the structured workflow should matter:

```text
05_medium_length_single_protagonist
07_dual_timeline_continuity
10_mystery_clue_fairness_smoke
```

Do not rely only on the original 3-chapter locked-room smoke test. It is too simple, and direct prompting may perform similarly.

## Success Criterion For The Skill Strategy

The full skill strategy is justified if it consistently improves at least two of:

- continuity
- reveal control
- traceability
- revision readiness
- clue or Codex grounding

It does not need to win on raw prose elegance in every run. A direct write can sometimes have smoother prose. The skill's claim is stronger process control for longform writing.

## Using Baseline Gaps To Improve The System

Baseline comparison is not only a proof exercise. It should also feed rule evolution.

When a baseline outperforms the full skill, record what happened:

```text
Did direct write produce more natural dialogue?
Did simple engineered writing preserve pacing better?
Did the full skill over-constrain prose?
Did beat-level writing fragment a scene that should flow continuously?
Did Codex context add irrelevant information?
```

When the full skill outperforms baselines, record which mechanism helped:

```text
Did summary_after preserve a clue?
Did beat validation prevent early reveal?
Did relevant Codex keep a character role stable?
Did manifest trace make the failure easier to localize?
```

Each comparison should produce one of three improvement signals:

### Writer Rule Improvement

Use when baseline prose is better but the full skill is more controlled.

Examples:

- add smoother scene-continuation instructions
- reduce mechanical beat boundaries in prose
- improve dialogue style rules
- avoid over-explaining Codex facts

### Workflow Rule Improvement

Use when the full skill fails because an intermediate representation is missing or too weak.

Examples:

- add clue-state tracking
- make chapter summaries distinguish event time from reveal time
- require `required_codex` for supporting-character beats
- add protected reveal redaction for a new pattern

### Evaluator Rule Improvement

Use when a run has a visible issue but the report passes it.

Examples:

- add positive checks for final reveal fulfillment
- require evidence for clue-fairness claims
- detect premature reveal in prose prompts and in planning prompts separately
- make judge checks semantic instead of only keyword-based

In this way, direct-write and simple-engineered baselines become a source of pressure for improving both the writer and the judge.

The full skill should not defend complexity for its own sake. If a simple baseline repeatedly matches the full skill on a class of tasks, either:

- simplify the workflow for that class, or
- add a stronger testcase where the structured workflow's advantage is measurable.

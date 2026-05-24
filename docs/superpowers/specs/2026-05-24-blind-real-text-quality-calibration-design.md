# Blind Real Text Quality Calibration Design

## Goal

Phase D0.5 evaluates real manuscript quality, not workflow traceability.

The task uses existing 05/07/10 samples with three writing methods:

- direct write;
- simple engineered;
- full longform-writing skill.

The methods are hidden from evaluators as Sample A/B/C. Two internal evaluator agents judge the same blind samples:

- Rubric Judge: uses `longform_text_quality_rubric_v1`.
- Reader/Editor Judge: uses direct editorial reading judgment without the full rubric.

The main thread reveals the hidden mapping after evaluation and writes a comparison report.

## Non-Goals

- Do not implement chapter revision loop.
- Do not use DeepSeek or any external API judge.
- Do not use engineering traceability as text-quality victory.
- Do not assume full skill must win.

## Evaluation Focus

Longform consistency is treated as reader-visible text quality, not as artifact existence.

The blind evaluation asks:

- Which manuscript reads better as a longform story?
- Which manuscript carries chapter-to-chapter state, emotion, clues, and payoff best?
- Does full skill's context management translate into better real text?
- Does full skill become mechanical compared with direct/simple baselines?
- Is the rubric aligned with free reader/editor judgment?

## Samples

Use existing outputs only:

- `05_medium_length_single_protagonist`
- `07_dual_timeline_continuity`
- `10_mystery_clue_fairness_smoke`

For each case:

- direct-write manuscript;
- simple-engineered manuscript;
- full-skill manuscript.

Blind package layout:

```text
blind_quality_eval_runs/phase_d0_5/
  public/case_05/{request.md,sample_A.md,sample_B.md,sample_C.md}
  public/case_07/{request.md,sample_A.md,sample_B.md,sample_C.md}
  public/case_10/{request.md,sample_A.md,sample_B.md,sample_C.md}
  private_mapping.json
```

Evaluators receive only the `public` directory and must not inspect baseline or integrated run paths.

## Rubric Judge Output

Rubric Judge uses `longform-writing/references/longform_text_quality_rubric_v1.md`.

For each case and sample, it returns:

- dimension scores 1-5;
- concrete evidence;
- issue;
- revision target;
- longform quality eligibility.

It also ranks A/B/C for each case and comments on whether the rubric captured meaningful differences.

## Reader/Editor Judge Output

Reader/Editor Judge receives only the request and samples.

It returns:

- ranking A/B/C for each case;
- which manuscript reads best;
- which manuscript is most coherent as longform prose;
- which manuscript has best local prose flow;
- which manuscript feels most mechanical;
- concrete evidence;
- revision advice for the weaker manuscripts.

## Iteration Rule

Main thread checks evaluator outputs.

Rerun or revise prompts only if:

- rankings are missing;
- evidence is generic;
- evaluator discusses workflow traceability instead of text;
- evaluator identifies methods instead of treating samples blind;
- revision targets are absent or not actionable.

Limit to 2-3 iterations.

## Success Criteria

The task succeeds if the final report can answer:

- whether full skill improves real text quality compared with direct/simple;
- whether direct/simple have prose advantages worth absorbing;
- whether rubric and free reader judgment agree or conflict;
- which rubric dimensions are useful for V1 revision loop;
- which text-quality dimensions V1 should optimize first.

Full skill does not need to win for the task to succeed.

## Deliverables

- blind sample package under ignored `blind_quality_eval_runs/`;
- evaluator outputs captured in the final tracked report;
- `longform_text_quality_rubric_v1.md`;
- `design_context/25_blind_real_text_quality_calibration_report.md`;
- optional rubric update recommendations for V1 revision loop.

# Phase B/C Integration Report

## Scope

This integration started from `main@cd303bd` and merged two independent branches:

- `phase-b-complexity`: complex validation for cases 05-07, while preserving 01-04.
- `phase-c-genre-routing`: dynamic genre adapter routing for cases 08-10, while preserving 01-04.

The merged skill now supports:

- longer single-protagonist continuity pressure;
- supporting-cast Codex routing;
- dual-timeline memory and reveal control;
- romance, fantasy, and mystery/clue-fairness prompt adapters;
- baseline comparison controls for direct writing and simple engineered writing.

## Integrated Acceptance

All full-skill acceptance cases 01-10 passed on the merged main worktree.

| Case | Run dir | Result |
| --- | --- | --- |
| 01 single protagonist choice room | `runs/integrated_01` | Pass |
| 02 continuity smoke | `runs/integrated_02` | Pass |
| 03 beat validation guard | `runs/integrated_03` | Pass |
| 04 checkpoint interaction | `runs/integrated_04` | Pass |
| 05 medium-length single protagonist | `runs/integrated_05_v2` | Pass |
| 06 supporting-cast Codex routing | `runs/integrated_06` | Pass |
| 07 dual-timeline continuity | `runs/integrated_07_v4` | Pass |
| 08 romance adapter | `runs/integrated_08` | Pass |
| 09 fantasy adapter | `runs/integrated_09` | Pass |
| 10 mystery clue fairness | `runs/integrated_10` | Pass |

Each listed run reported:

```text
Pass / Fail: Pass
Critical Failures: None
```

## Fixes During Integration

The Phase C merge initially conflicted with Phase B in `run_acceptance.py`. The final runner keeps both sets of behavior:

- Phase B requested chapter-count parsing, Codex normalization, reveal redaction, content checks, and chapter draft finalization.
- Phase C genre adapter selection, adapter prompt slots, genre Codex insertion, clue-state memory, and genre prompt checks.

Additional integration fixes:

- Removed a duplicate `finalize_chapter_draft` definition that caused Phase B finalization to be overridden by Phase C.
- Added a Phase B 07 chapter-four finalization marker for `承担责任`.
- Added a Phase B 07 beat-level fallback that explicitly marks `现在` in dual-timeline intermediate representation.
- Skipped genre adapter checks for the expected validation-guard stop case.
- Avoided false stage mismatch on the checkpoint-interaction smoke case.

## Baseline Controls

`longform-writing/scripts/run_baseline_comparison.py` now runs the 11-12 baseline controls:

```text
direct write
simple engineered write
full longform-writing skill
```

The comparison was run against:

- `05_medium_length_single_protagonist`
- `07_dual_timeline_continuity`
- `10_mystery_clue_fairness_smoke`

Generated baseline artifacts are under `baseline_runs/` and ignored by git. The aggregate report is:

```text
baseline_runs/comparison_report.md
baseline_runs/comparison_report.json
```

Observed summary:

| Case | Direct write | Simple engineered | Full skill |
| --- | --- | --- | --- |
| 05 | Fail | Fail | Pass |
| 07 | Fail | Fail | Pass |
| 10 | Fail | Fail | Pass |

## Improvement Signals

Writer rule:

- Compare simple baseline prose against full-skill prose in later iterations. If simple prose is smoother, reduce mechanical beat-boundary artifacts without weakening validation.

Workflow rule:

- Preserve explicit memory, protected reveal checks, Codex/clue-state grounding, and manifest trace. These mechanisms were the main measured advantage over baselines.
- Keep dual-timeline intermediate artifacts explicit: every chapter plan/beat should distinguish present action from past evidence.

Evaluator rule:

- Keep traceability as a separate process-quality dimension rather than only judging final prose.
- Add stronger semantic checks later if keyword heuristics become too brittle.

## Remaining Risks

- Baseline judging is currently deterministic and heuristic. It is useful for regression pressure, but not yet a full literary-quality judge.
- The full skill passes structural/process checks; prose quality should still be evaluated by a separate LLM judge rubric in the next revision loop.
- The current genre adapter set is small: romance, fantasy, mystery/clue fairness, locked-room moral trial, and general fiction.

## Next Phase Note: Chapter Review Quality Comparison

When adding the chapter review / revision loop, include a quality comparison track in the same phase.

Reason:

- If `direct write` or `simple engineered` can consistently match the full skill on final prose quality, the full workflow must either justify its complexity through better control/revision or be simplified.
- Current baseline controls mainly prove process advantages: continuity, reveal control, clue/Codex grounding, and traceability.
- They do not yet prove that full-skill prose is better than simpler baselines.

Required addition for the chapter review phase:

```text
For the same testcase, compare:
1. direct-write manuscript
2. simple-engineered manuscript
3. full-skill manuscript before chapter review
4. full-skill manuscript after chapter review/revision
```

Use a shared LLM judge rubric for text quality:

- Story Foundation
- Narrative Arc
- Structural Progression
- Pacing
- Characterization
- Dialogue
- POV Control
- Genre Fulfillment
- Reader Engagement

The judge must output scores with evidence, not general praise.

The phase should report two separate conclusions:

```text
Process-control conclusion:
Does the full skill improve continuity, reveal control, clue state, Codex grounding, and traceability?

Text-quality conclusion:
Does chapter review actually improve the final manuscript compared with direct/simple baselines?
```

If the simple baselines match or beat the reviewed full-skill manuscript on quality, record the gap as a Writer Rule or Workflow Simplification signal rather than defending the complex workflow by default.

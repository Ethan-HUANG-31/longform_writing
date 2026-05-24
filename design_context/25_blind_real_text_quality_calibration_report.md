# Phase D0.5 Blind Real Text Quality Calibration Report

## Purpose

This calibration tests real manuscript quality, not engineering traceability.

The question was whether the current longform-writing skill actually produces better longform fiction than simpler baselines, and whether `longform_text_quality_rubric_v1` is strong enough to support a future chapter revision loop.

## Setup

Three existing cases were evaluated:

- `05_medium_length_single_protagonist`
- `07_dual_timeline_continuity`
- `10_mystery_clue_fairness_smoke`

Each case had three blind samples:

- direct write
- simple engineered
- full longform-writing skill

The blind sample package was generated under:

```text
blind_quality_eval_runs/phase_d0_5/
```

This directory is intentionally ignored by git because it contains temporary evaluation materials and a private mapping file.

Two internal evaluator agents were used:

- Rubric Judge: read `longform_text_quality_rubric_v1.md` and scored dimensions.
- Reader/Editor Judge: did not read the rubric and judged as an editor/target reader.

Both evaluators were instructed to read only public blind samples and not inspect source run directories or the private mapping.

## Blind Mapping

| Case | Sample A | Sample B | Sample C |
|---|---|---|---|
| case_05 | simple engineered | full skill | direct write |
| case_07 | full skill | direct write | simple engineered |
| case_10 | direct write | simple engineered | full skill |

## Rubric Judge Results

| Case | Blind Ranking | Revealed Ranking | Main Reason |
|---|---|---|---|
| case_05 | C > B > A | direct > full > simple | Direct had the best manuscript-level reading quality; full skill preserved continuity but became repetitive and procedural. |
| case_07 | A > B > C | full > direct > simple | Full skill completed the four-stage reveal arc; direct/simple had better local writing in places but were incomplete. |
| case_10 | A > C > B | direct > full > simple | Direct gave the most readable cozy mystery; full skill had fair-play structure but sounded schematic and repetitive. |

The rubric judge found the rubric useful. The eligibility rule correctly prevented attractive but incomplete manuscripts from winning longform quality. The strongest differentiating dimensions were:

- Longform Textual Continuity
- Narrative / Structural Progression
- Scene & Prose Flow
- Character & Emotional Arc

The weakest dimension was Revision Usefulness. It produced actionable targets, but should not be treated as a core quality score because a broken-but-fixable draft should not beat a currently stronger manuscript.

## Reader/Editor Judge Results

| Case | Blind Ranking | Revealed Ranking | Main Reason |
|---|---|---|---|
| case_05 | C > B > A | direct > full > simple | Direct had the strongest responsibility turn and read most like a complete short story. |
| case_07 | A > C > B | full > simple > direct | Full skill completed the required reveal sequence; simple had stronger local atmosphere than direct but was still incomplete. |
| case_10 | A > C > B | direct > full > simple | Direct had the best cozy mystery feel; full skill was structurally clearer than simple but mechanical. |

The reader/editor judge agreed with the rubric judge on all first-place samples:

- case_05: direct wins
- case_07: full skill wins
- case_10: direct wins

The only material disagreement was the order of second and third place in case_07. The reader/editor judge valued simple engineered sample C's local atmosphere over direct sample B, while the rubric judge valued direct sample B's stronger dialogue and pressure. Both still agreed neither B nor C completed the required longform arc.

## Main Finding

The full skill does not yet consistently win on real text quality.

It wins when the test depends heavily on longform completion and staged continuity, as in case_07. But in case_05 and case_10, direct writing produced more natural prose, better local scene movement, and more satisfying reader experience.

This does not invalidate the longform workflow. It clarifies the current tradeoff:

- Full skill is better at maintaining requirements, chapter coverage, clue continuity, and complete arc execution.
- Direct write can be better at prose flow, emotional naturalness, dialogue rhythm, and avoiding mechanical repetition.
- Simple engineered is usually weaker than both for these samples because it often fails completion or payoff.

Therefore the V1 value is not "prove full skill already writes better." The value is:

```text
Use the structured workflow to preserve longform control,
then add revision loops that recover the naturalness and local scene quality
that direct writing sometimes has.
```

## Text-Quality Issues Found In Full Skill

Recurring weaknesses in full-skill outputs:

- Repeated physical inspection beats: papers, margins, notes, cards, and screens are checked too many times.
- Visible beat expansion: scenes sometimes read like task execution rather than continuous fiction.
- Summary-like emotional conclusions: character realization is stated after evidence rather than dramatized through pressure.
- Weak dialogue pressure: dialogue often transmits evidence instead of creating conflict or subtext.
- Procedural clue payoff: especially in mystery, clue chains are correct but not elegant or emotionally alive.

These are reader-visible text-quality issues, not workflow issues.

## Direct/Simple Advantages To Absorb

Direct writing sometimes provided:

- cleaner scene flow;
- less repeated deduction;
- more natural emotional turns;
- stronger local dialogue rhythm;
- more compact exposition.

Simple engineered did not win overall, but it sometimes had stronger atmosphere in openings. This suggests the future revision loop should not only check structure; it should also improve sentence-level and scene-level reading experience.

## Rubric Calibration Result

`longform_text_quality_rubric_v1` is adequate as the first fixed value system for V1 chapter revision loop design, with one caveat.

Use it as:

- a chapter/manuscript quality judge;
- a source of actionable revision targets;
- a way to compare full skill against baselines on real text quality.

Do not use it as:

- a reward for engineering artifacts;
- a proof that a workflow is better because it has more intermediate files;
- a fully mature literary value system.

The current rubric should remain general-purpose. Genre-specific overlays can be added later, but the next iteration should first prove that the generic rubric can drive useful revisions.

## V1 Revision Loop Priorities

The next longform-writing skill iteration should add chapter-level review and rewrite loops that optimize the following, in order:

1. Remove repetition and mechanical evidence logging.
2. Turn beat-by-beat execution into continuous scene prose.
3. Convert clues and facts into character pressure instead of summary conclusions.
4. Improve dialogue so it advances conflict, not just information.
5. Preserve longform continuity while making genre payoff feel elegant and human.

The acceptance standard for V1 should require that a revised full-skill draft is not merely more compliant than direct/simple baselines, but visibly better in reader-facing text quality on at least the main failed dimensions above.

## Recommendation

Proceed to V1 chapter revision loop only after treating this report as the quality baseline.

The first V1 validation should compare:

- unrevised full-skill draft;
- revised full-skill draft;
- direct baseline;
- simple engineered baseline.

The revised full-skill draft should be expected to keep full skill's longform control while reducing the mechanical prose weaknesses identified here.

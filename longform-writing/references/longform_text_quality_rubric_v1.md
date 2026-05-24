# Longform Text Quality Rubric V1

This rubric evaluates real manuscript quality for longform fiction.

It is a general-purpose meta-rubric, not a locked-room-specific rubric. Genre-specific overlays may be added later, but V1 should first test this general rubric across different story shapes.

Do not treat engineering artifacts as text quality. Judge what a reader can experience in the manuscript.

## Output Requirements

For every sample, score each dimension from 1 to 5.

Every dimension must include:

- `score`;
- concrete `evidence` from the manuscript;
- `issue`, or empty string if no material issue;
- `revision_target`, or empty string if no revision is needed.

Do not use generic praise. Evidence must point to a visible textual behavior, not the existence of workflow files.

## Eligibility Rule

`is_longform_quality_eligible` is false if any of these are below 3:

- Longform Textual Continuity;
- Story Foundation;
- Narrative / Structural Progression.

A manuscript can have attractive local prose and still fail longform quality if it does not read like a coherent longform story.

## Calibration Notes

Phase D0.5 blind evaluation showed that the rubric should be used as a real text-quality judge, not as a workflow-compliance judge.

Useful dimensions:

- Longform Textual Continuity separated complete longform manuscripts from attractive but incomplete openings.
- Scene & Prose Flow exposed mechanical beat expansion, repeated object handling, and visible prompt-step stitching.
- Character & Emotional Arc exposed whether clue chains became personal pressure or remained procedural.

Known limitation:

- Revision Usefulness is a support dimension, not a quality dimension. It should not decide the winner when two manuscripts differ mainly in current reading quality. Use it to identify whether a chapter revision loop can improve the draft, not to reward fixability over an already better manuscript.

For V1 chapter revision loops, the primary optimization targets should be concrete reader-visible weaknesses: repeated deductions, mechanical evidence logging, summary-like emotional conclusions, weak dialogue pressure, and genre payoff that is structurally correct but not yet elegant.

## Dimensions

### 1. Longform Textual Continuity

Reader-visible continuity across chapters, scenes, character state, emotional state, clues, objects, promises, and payoffs.

- `1`: Chapters read like unrelated standalone generations. Earlier events, emotions, or clues are barely inherited.
- `2`: Some prior facts are mentioned, but character state, clues, or emotional consequences often reset.
- `3`: Main facts continue, but chapter transitions feel mechanical or cumulative emotion is thin.
- `4`: Earlier events, character state, and clues naturally shape later chapters.
- `5`: The manuscript creates strong cumulative pressure; earlier material keeps returning with new emotional, informational, or thematic force.

### 2. Story Foundation

Core concept, premise conflict, central dramatic question, and theme through choices.

- `1`: The story core is unclear or inert.
- `2`: The core concept is visible, but conflict is weak or the manuscript often drifts.
- `3`: Core concept and conflict are understandable, but theme or central pressure is uneven.
- `4`: The manuscript consistently serves a clear story core through conflict and choice.
- `5`: The premise is compelling, sustained, and deepened through concrete irreversible choices.

### 3. Narrative / Structural Progression

Whether the manuscript has meaningful setup, complication, escalation, and changed end state.

- `1`: Events are piled up without clear direction.
- `2`: Events have order, but many scenes or chapters lack function.
- `3`: Basic progression exists, but some chapters repeat or under-develop turns.
- `4`: Major chapters/scenes have clear functions and cause information, relationship, or state changes.
- `5`: Structure is tight, causal, and escalating; each chapter meaningfully changes the story.

### 4. Character & Emotional Arc

Character desire, fear, flaw, pressure choices, and emotional development.

- `1`: Characters are labels or tools.
- `2`: Characters have traits, but choices and emotions feel imposed by plot.
- `3`: Motivation is understandable, but change is jumpy or over-explained.
- `4`: Desire, fear, flaw, and pressure choices are visible in action.
- `5`: Character contradiction, emotional accumulation, and transformation are tightly integrated with plot pressure.

### 5. Scene & Prose Flow

Whether beats and scenes read as continuous prose rather than task execution.

- `1`: The manuscript reads like outline expansion; paragraphs and scenes are disconnected.
- `2`: Events are understandable, but prose is mechanical, jumpy, or explanation-heavy.
- `3`: Scenes are basically coherent, but beat-stitching or repeated actions are visible.
- `4`: Paragraphs and scenes flow naturally through action, perception, reaction, and consequence.
- `5`: Structure disappears into prose; the reader experiences continuous scenes rather than generation steps.

### 6. Pacing

Speed, emphasis, information release, repetition, and emotional space.

- `1`: Clearly padded, repetitive, rushed, or hard to finish.
- `2`: Pacing problems repeatedly interrupt reading.
- `3`: Readable but uneven or too uniform.
- `4`: Fast and slow passages are balanced; key turns receive space and ordinary actions are compressed.
- `5`: Pacing strongly drives tension, emotion, and genre experience.

### 7. Dialogue & Voice

Character-specific speech, conflict, subtext, and dialogue function.

- `1`: Dialogue is generic exposition, filler, or template speech.
- `2`: Dialogue conveys information but has weak voice, conflict, or subtext.
- `3`: Dialogue serves the plot but has limited character differentiation or pressure.
- `4`: Dialogue advances information, relationship, and conflict with clear character voices.
- `5`: Dialogue has layered subtext, distinct voices, pressure, and rhythm; what is unsaid matters.

### 8. Tension / Reader Engagement

Whether the manuscript creates real desire to continue reading.

- `1`: Little conflict, curiosity, or emotional pull.
- `2`: Surface suspense exists, but reading drive is weak or abstract.
- `3`: Basic momentum exists, but turns or reveals are inconsistent.
- `4`: Conflict, information gaps, and emotional pressure sustain interest.
- `5`: The manuscript consistently creates concrete questions, pressure, and anticipation.

### 9. Genre Fulfillment

Whether the manuscript fulfills its genre promise at a general level.

- `1`: Genre experience is absent or contradicted.
- `2`: Genre markers appear, but core reader experience is weak.
- `3`: Genre is recognizable but uneven in mechanism, pacing, or payoff.
- `4`: Genre promise is mostly fulfilled and tied to character/plot.
- `5`: Genre mechanism, emotional experience, reader expectation, and character choice reinforce each other.

### 10. Revision Usefulness

Whether the manuscript has identifiable, actionable improvement paths for a chapter revision loop.

- `1`: Problems are global and tangled; local revision is unlikely to help.
- `2`: Many issues are fixable only through broad restructuring.
- `3`: Some local revision targets exist, but they require careful preservation of structure.
- `4`: Main problems are clearly localizable and suitable for chapter-level revision.
- `5`: The manuscript is stable; a few targeted revisions could produce meaningful quality gains.

## Required Per-Sample JSON Shape

```json
{
  "sample_id": "A",
  "overall_score": 3.6,
  "is_longform_quality_eligible": true,
  "dimension_scores": {
    "longform_textual_continuity": {
      "score": 4,
      "evidence": ["specific textual evidence"],
      "issue": "",
      "revision_target": ""
    }
  },
  "top_strengths": [],
  "top_weaknesses": [],
  "revision_targets": [],
  "ranking_rationale": ""
}
```

# Quality Rubric V1

This rubric is the fixed evaluation value system for the first chapter review / revision loop.
It is derived from `NovelCrafter Developmental Editor 写作评价准则拆解.md`, adapted from human editor advice into an LLM-judge-friendly scoring format.

V1 uses this rubric as a stable judge. Do not let the judge rewrite or evolve this rubric during a writing run.

## Scope

This rubric evaluates two different things:

1. **Literary Quality**: whether the chapter or manuscript works as fiction.
2. **Workflow Control**: whether the chapter preserves longform-writing constraints such as beat fidelity, continuity, Codex grounding, reveal control, and revision safety.

The judge must keep these conclusions separate. A chapter may be readable but unsafe, or safe but dull.

## Scoring Scale

Use integer scores from 1 to 5.

- `1`: severe failure; the dimension is mostly absent or actively harmful.
- `2`: weak; visible problems affect the chapter's purpose or reader experience.
- `3`: usable; the dimension works at a basic level but has clear limitations.
- `4`: strong; the dimension works well with only minor issues.
- `5`: excellent; the dimension is consistently effective and specific to the story.

Every score must include concrete evidence. Do not give a score from general impression alone.

## Literary Quality Dimensions

### 1. Story Foundation

Question: Does the text serve a clear, compelling story core?

Checks:

- The core concept is clear and consistently executed.
- The premise creates conflict, pressure, or unavoidable choice.
- The central dramatic question remains visible at the appropriate scale.
- Theme emerges through plot and character choices rather than explanation.

Score anchors:

- `1`: The chapter does not reveal what story it belongs to, or the premise is inert.
- `2`: The concept is present but weakly connected to the chapter's events.
- `3`: The concept and conflict are understandable, but theme or central pressure is thin.
- `4`: The chapter clearly serves the story core and expresses pressure through choices.
- `5`: The chapter intensifies the core premise and expresses theme through specific irreversible choices.

### 2. Narrative Arc

Question: Does the text have a visible setup, complication, and movement toward resolution?

Checks:

- The chapter has a clear stage function within the larger story.
- Stakes escalate or become more specific.
- Turning points alter what the protagonist knows, wants, risks, or can do.
- The ending state differs meaningfully from the opening state.

Score anchors:

- `1`: Events are unordered or flat; there is no arc.
- `2`: Some events happen, but escalation and consequence are weak.
- `3`: The chapter has a basic arc but limited escalation.
- `4`: The chapter moves through clear setup and complication into a changed state.
- `5`: The chapter's arc strongly advances the larger story and sharpens future stakes.

### 3. Structural Progression

Question: Do scenes and beats create meaningful change rather than filler?

Checks:

- Each major scene has a purpose.
- Each major scene changes information, relationship, goal, risk, or emotional position.
- Transitions are logical.
- The sequence builds tension instead of repeating the same state.

Score anchors:

- `1`: Most scenes could be removed without changing the story.
- `2`: Some scenes have purpose, but repetition or dead space dominates.
- `3`: Important scenes move the story, but some passages stall or repeat.
- `4`: Most scenes create meaningful change and connect logically.
- `5`: Every major scene is necessary, sequenced for pressure, and changes story state.

### 4. Pacing

Question: Does the text control speed, emphasis, and emotional space effectively?

Checks:

- Important turns receive enough space for impact.
- Mundane or repeated actions are compressed.
- Sentence and paragraph rhythm vary with tension.
- The text avoids both rushed summary and stagnant over-description.
- Pacing fits the genre.

Score anchors:

- `1`: The chapter is clearly rushed, padded, repetitive, or hard to finish.
- `2`: Pacing problems distract from the story.
- `3`: Pacing is readable but uneven or mechanically uniform.
- `4`: Pacing mostly supports tension, reflection, and information release.
- `5`: Pacing creates strong momentum while giving major turns the right emotional weight.

### 5. Characterization

Question: Do characters feel driven by desire, fear, flaw, and pressure-tested choices?

Checks:

- The protagonist's desire, fear, and flaw can be inferred from action.
- Choices under pressure reveal character.
- Internal thought and external action align or contradict meaningfully.
- Character change feels earned.
- Supporting characters have functional specificity, not interchangeable labels.

Score anchors:

- `1`: Characters are labels or plot devices.
- `2`: Characters have stated traits but weak action-based motivation.
- `3`: Main characters are understandable, but change or pressure choices are thin.
- `4`: Character motives and flaws show through concrete choices.
- `5`: Character desire, fear, flaw, contradiction, and change are tightly integrated with plot pressure.

### 6. Dialogue

Question: Does dialogue advance conflict, character, relationship, or information?

Checks:

- Speech reflects character background, role, emotion, and situation.
- Dialogue does more than explain information.
- Dialogue contains conflict, subtext, avoidance, or pressure.
- Dialogue is balanced with action, reaction, and interiority.
- Greetings, obvious statements, and exposition are controlled.

Score anchors:

- `1`: Dialogue is mostly exposition, generic speech, or filler.
- `2`: Dialogue communicates information but has weak voice or conflict.
- `3`: Dialogue has some function and voice, but limited subtext.
- `4`: Dialogue advances story while revealing character and pressure.
- `5`: Dialogue works on multiple levels: conflict, subtext, relationship, information, and rhythm.

### 7. POV / Narrative Distance

Question: Does viewpoint remain stable and serve emotional effect and information control?

Checks:

- POV remains consistent unless a deliberate shift is clearly signaled.
- The narration does not reveal private knowledge outside the allowed viewpoint.
- Narrative distance fits the genre and scene pressure.
- The chosen viewpoint contributes unique information or emotional effect.

Score anchors:

- `1`: POV is confusing or repeatedly leaks impossible knowledge.
- `2`: POV is mostly identifiable but unstable or intrusive.
- `3`: POV is basically stable, with occasional distance/control issues.
- `4`: POV is stable and supports suspense, emotion, or limited knowledge.
- `5`: POV and narrative distance are precise tools for pressure, intimacy, and reveal control.

### 8. Genre Fulfillment

Question: Does the text satisfy the current genre promise?

Checks:

- The chapter uses the selected genre adapter's core expectations.
- Genre mechanisms are internally consistent.
- Genre elements shape character choices rather than existing as decoration.
- Genre pacing and emotional payoffs match reader expectations.

Score anchors:

- `1`: The genre promise is absent or contradicted.
- `2`: Genre markers appear, but the core experience is weak.
- `3`: The genre is recognizable but uneven.
- `4`: The genre promise is mostly fulfilled and connected to plot/character.
- `5`: Genre mechanisms, reader expectations, and character choices reinforce each other.

## Workflow Control Dimensions

### 9. Beat Fidelity

Question: Does the prose fulfill the planned beats without skipping, overextending, or contradicting them?

Score anchors:

- `1`: The prose ignores or contradicts major beats.
- `2`: Several beats are missing, distorted, or written out of order.
- `3`: Most beats are present but some are shallow or overextended.
- `4`: Beats are faithfully expanded with minor omissions.
- `5`: Beats are fully and proportionally dramatized without writing beyond scope.

### 10. Continuity

Question: Does the text preserve established facts, memory, timeline, object states, and clue states?

Score anchors:

- `1`: Major continuity errors make the story incoherent.
- `2`: Important facts, roles, or timeline states drift.
- `3`: Continuity is mostly preserved, with minor gaps.
- `4`: Prior facts are used correctly and consistently.
- `5`: Continuity is actively leveraged to create cumulative pressure and payoff.

### 11. Reveal Control

Question: Does the text protect delayed information and fulfill required reveals at the right time?

Score anchors:

- `1`: Protected reveals are leaked early or required reveals are absent.
- `2`: Reveal timing is unclear or partially broken.
- `3`: Reveal control is mostly safe but weakly dramatized or under-explicit.
- `4`: Reveals are timed correctly and clearly written.
- `5`: Reveal timing, clue preparation, and emotional payoff are precise and effective.

### 12. Codex Grounding

Question: Does the text obey the story bible for characters, locations, rules, objects, and style constraints?

Score anchors:

- `1`: The text contradicts key Codex facts.
- `2`: Several Codex facts are missing, generic, or misused.
- `3`: Codex grounding is adequate but shallow.
- `4`: Relevant Codex details are used correctly and naturally.
- `5`: Codex details shape action, conflict, and prose without exposition overload.

### 13. Revision Safety

Question: If this is a revised draft, does the revision improve the chapter without breaking constraints?

For non-revised drafts, judge whether the text is safe to revise locally.

Score anchors:

- `1`: Revision would require global rewriting or already breaks core constraints.
- `2`: Local revision risks breaking continuity, reveal timing, POV, or Codex facts.
- `3`: Local revision is possible, but preserve constraints must be explicit.
- `4`: Problems are localizable and revision can be targeted safely.
- `5`: Revision targets are clear, local, and unlikely to disturb downstream memory.

## Blocking Rules

Use these rules to decide `revision_required` and `blocking_issues`.

- Any Workflow Control dimension with `score <= 2` is blocking.
- Reveal Control with `score <= 3` is blocking.
- POV / Narrative Distance with `score <= 2` is blocking.
- Any Literary Quality dimension with `score <= 2` is blocking if it prevents the chapter from fulfilling its story purpose.
- Overall weighted score below `3.5` requires revision unless all issues are explicitly non-actionable.
- If a judge cannot cite evidence for a low score, it must not mark the issue as blocking.

## Revision Target Rules

Revision targets must be actionable.

Good target:

```text
Compress the repeated hallway hesitation in the middle third and replace one repetition with a concrete new piece of evidence from the report.
```

Bad target:

```text
Make the pacing better.
```

Every revision target must include:

- location or scope;
- problem;
- intended change;
- preserve constraint, if relevant.

## Required JSON Shape

```json
{
  "rubric_version": "quality_rubric_v1",
  "target": {
    "case_name": "",
    "method": "",
    "unit": "chapter_or_manuscript",
    "genre_adapter": ""
  },
  "scores": {
    "literary_quality": {
      "story_foundation": {
        "score": 3,
        "evidence": ["concrete textual evidence"],
        "issue": "specific issue or empty string",
        "revision_target": "specific revision target or empty string",
        "blocking": false
      }
    },
    "workflow_control": {
      "beat_fidelity": {
        "score": 3,
        "evidence": ["concrete textual evidence"],
        "issue": "specific issue or empty string",
        "revision_target": "specific revision target or empty string",
        "blocking": false
      }
    }
  },
  "overall": {
    "literary_score": 3.0,
    "control_score": 3.0,
    "weighted_score": 3.0,
    "revision_required": true,
    "summary": "one concise judgment"
  },
  "blocking_issues": [
    {
      "dimension": "reveal_control",
      "location": "chapter 1",
      "issue": "protected reveal appears too early",
      "evidence": "short evidence",
      "suggested_fix": "specific safe fix"
    }
  ],
  "calibration_notes": {
    "distinguishes_method_quality": true,
    "possible_false_positive": "",
    "possible_false_negative": ""
  }
}
```

The full implementation should include all eight literary dimensions and all five workflow control dimensions under the same shape.
